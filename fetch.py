#!/usr/bin/python

import subprocess
import json
import csv
import os
from datetime import datetime, timedelta
import time
import sys
import re

def log(message):
  print("[log] " + message)

def error(message):
  exit("[error] " + message)

def mysql(config, command):
  result = ["mysql"]
  if config.has_key("mysql_username"):
    result.append("-u" + config["mysql_username"])
  if config.has_key("mysql_password"):
    result.append("-p" + config["mysql_password"])
  result.append("-e")
  result.append(command)
  return result

def mysqldump(config, database):
  result = ["mysqldump"]
  if config.has_key("mysql_username"):
    result.append("-u" + config["mysql_username"])
  if config.has_key("mysql_password"):
    result.append("-p" + config["mysql_password"])
  result.append(database)
  return result

# Get current install path from config
if len(sys.argv) < 2:
  error("Please provide the current path as a command-line argument.")
path = sys.argv[1]

# Add a trailing slash if necessary
if path[-1] != "/":
  path += "/"

# Read config file
if not os.path.isfile(path + "config"):
  error("Config file does not exist.")
config = {}
with open(path + "config", "r") as file:
  lines = file.readlines()
  for line in lines:
    if len(line) < 1:
      continue
    line = line.split("#")[0].strip()
    if len(line) < 1:
      continue
    parts = line.split(":")
    if len(parts) != 2:
      error("Invalid config file syntax. Each line must be blank, a comment (#), or a key-value pair (key: value).")
    config[parts[0].strip()] = parts[1].strip()

# Get database from config
database = config.get("mysql_database", "finances")
backup_hours = int(config.get("backup_hours", "12"))

def escape(string):
  if "," in string:
    return "\"" + string + "\""
  return string

def standardize_newlines():
  with open(path + "transactions.csv", "r") as file:
    lines = file.readlines()
  with open(path + "transactions.csv", "w") as file:
    for line in lines:
      file.write(line.replace("\r\n", "\n"))
  with open(path + "accounts.csv", "r") as file:
    lines = file.readlines()
  with open(path + "accounts.csv", "w") as file:
    for line in lines:
      file.write(line.replace("\r\n", "\n"))

def output_accounts_csv(accounts):
  log("Generating accounts csv file.")
  with open(path + "accounts.csv", "w") as file:
    file.write("id, plaid_id, user, available_balance, current_balance, institution_type, name, number, subtype, type, item, \n")
    writer = csv.writer(file, delimiter = ',',  quotechar = '"', quoting = csv.QUOTE_MINIMAL)
    for account in accounts:
      writer.writerow(map(lambda x: x.encode('utf8'), [
        "0",
        account["_id"],
        account["_user"],
        str(account["balance"]["available"]),
        str(account["balance"]["current"]),
        account["institution_type"],
        account["meta"]["name"],
        account["meta"]["number"],
        account["subtype"],
        account["type"],
        account["_item"],
        ""
      ]))

def backup_transactions_csv():
  log("Backing up transactions csv file.")
  if not os.path.isdir(path + "backups"):
    subprocess.call(["mkdir", path + "backups"])
  now = int(time.time())
  if os.path.isfile(path + "transactions.csv"):
    subprocess.call(["cp", path + "transactions.csv", path + "backups/transactions-backup-%d.csv" % now])

def delete_old_backups():
  log("Deleting backups from before %d hours ago." % backup_hours)
  for backup in os.listdir(path + "backups"):
    match = re.match(r"^transactions\-backup\-(\d+)\.csv$", backup)
    if not match:
      match = re.match(r"^mysql\-backup\-(\d+)\.sql$", backup)
    if match:
      epoch = float(match.group(1))
      created = datetime.fromtimestamp(epoch)
      delta = datetime.now() - created
      if delta > timedelta(hours = backup_hours):
        os.remove(path + "backups/" + backup)

def output_transactions_csv(transactions):
  log("Generating transactions csv file.")
  existing_ids = []
  existing_categories = {}

  # Uncomment this to load category information from data.csv
  # with open("data.csv", "r") as file:
  #   rows = csv.reader(file, delimiter = ',', quotechar = '"')
  #   for row in rows:
  #     existing_categories[(row[2], -float(row[6]))] = (row[7], row[8])

  if os.path.isfile(path + "transactions.csv"):
    with open(path + "transactions.csv", "r") as file:
      rows = csv.reader(file, delimiter = ',', quotechar = '"')
      for row in rows:
        if len(row) > 3:
          existing_ids.append(row[-3])
  with open(path + "transactions.csv", "a") as file:
    if len(existing_ids) == 0:
      file.write("id, posted, reference_number, payee, amount, category, keywords, pending, plaid_id, plaid_account_id,")
    writer = csv.writer(file, delimiter = ',',  quotechar = '"', quoting = csv.QUOTE_MINIMAL)
    newline = True
    for transaction in transactions:
      if transaction["_id"] not in existing_ids:
        if newline:
          newline = False
          file.write("\n")
        print(("[add] transaction for $%.2f to %s" % (transaction["amount"], transaction["name"])).encode('utf8'))
        (category, keywords) = existing_categories.get((transaction["date"], transaction["amount"]), ("uncategorized", ""))
        writer.writerow(map(lambda x: x.encode('utf8'), [
          "0",
          transaction["date"],
          transaction.get("meta", {}).get("reference_number", ""),
          transaction["name"],
          str(transaction["amount"]),
          category,
          keywords,
          str(int(transaction["pending"])),
          transaction["_id"],
          transaction["_account"],
          ""
        ]))

def backup_mysql_data():
  log("Backing up mysql data.")
  backup = subprocess.check_output(mysqldump(config, database))
  now = int(time.time())
  with open(path + "backups/mysql-backup-%d.sql" % now, "w") as file:
    file.write(backup)

def load_mysql_data_from_csvs():
  log("Loading mysql data from generated csv files.")
  subprocess.call(mysql(config, """
    use %s;
    delete from transactions;
    LOAD DATA
      INFILE '%stransactions.csv'
      INTO TABLE transactions
      FIELDS TERMINATED BY ','
      ENCLOSED BY '"'
      LINES TERMINATED BY '\n'
      IGNORE 1 LINES;
  """ % (database, path)))
  subprocess.call(mysql(config, """
    use %s;
    delete from accounts;
    LOAD DATA
      INFILE '%saccounts.csv'
      INTO TABLE accounts
      FIELDS TERMINATED BY ','
      ENCLOSED BY '"'
      LINES TERMINATED BY '\n'
      IGNORE 1 LINES;
  """ % (database, path)))

def fetch_accounts_and_transactions():
  log("Fetching accounts and transactions via Plaid.")
  response = subprocess.check_output([
    "curl", "-X", "POST", "https://tartan.plaid.com/connect/get",
      "-d", "client_id=" + config["plaid_client_id"],
      "-d", "secret=" + config["plaid_secret"],
      "-d", "access_token=" + config["plaid_access_token"]
  ])

  response_json = json.loads(response)
  output_accounts_csv(response_json["accounts"])
  backup_transactions_csv()
  standardize_newlines()
  output_transactions_csv(response_json["transactions"])
  backup_mysql_data()
  load_mysql_data_from_csvs()
  delete_old_backups()

fetch_accounts_and_transactions()
