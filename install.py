#!/usr/bin/python

import sys
import subprocess
import os.path
import re
import json
from datetime import datetime

def log(message):
  print("[log] " + message)

def error(message):
  exit("[error] " + message)

def confirm(message):
  valid_answers = {
    "yes": True,
    "no": False,
    "y": True,
    "n": False
  }

  while True:
    response = raw_input(message + "\n> ").strip()
    if valid_answers.has_key(response):
      return valid_answers[response]
    else:
      print("Please answer yes or no.")

def mysql(config, command):
  result = ["mysql"]
  if config.has_key("mysql_username"):
    result.append("-u" + config["mysql_username"])
  if config.has_key("mysql_password"):
    result.append("-p" + config["mysql_password"])
  result.append("-e")
  result.append(command)
  return result

# Read config file
if not os.path.isfile("config"):
  error("Config file does not exist.")
config = {}
with open("config", "r") as file:
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

if config.has_key("template"):
  error("Please fill out the config file before running the install script.")

# Check required config items
if not config.has_key("install_path"):
  error("Config must provide an install location (install_path: [path]).")
if not config.has_key("plaid_client_id"):
  error("Config must provide a plaid client id (plaid_client_id: [id]).")
if not config.has_key("plaid_secret"):
  error("Config must provide a plaid secret (plaid_secret: [secret]).")
if not config.has_key("plaid_access_token"):
  if not config.has_key("bank_username"):
    error("Config must provide a bank username (bank_username: [username]) or an access token (access_token: [token]).")
  if not config.has_key("bank_password"):
    error("Config must provide a bank password (bank_password: [password]) or an access token (access_token: [token]).")
  if not config.has_key("bank_password"):
    error("Config must provide a bank type (bank_type: [type]).")
log("Config file read.")

# Get install path from config file
path = config["install_path"]

# Add a trailing slash if necessary
if path[-1] != "/":
  path += "/"

# Ensure install path exists
if not os.path.isdir(path):
  error("Provided install location '" + path +"' does not exist.")
log("Install path verified.")

# Creating Plaid User (if no access_token is provided)
if not config.has_key("plaid_access_token"):
  if confirm("No access token was provided. Would you like to create a Plaid User?"):
    try:
      response = subprocess.check_output([
          "curl", "-X", "POST", "https://tartan.plaid.com/connect",
            "-d", "client_id=" + config["plaid_client_id"],
            "-d", "secret=" + config["plaid_secret"],
            "-d", "username=" + config["bank_username"],
            "-d", "password=" + config["bank_password"],
            "-d", "type=" + config["bank_type"]
          ])
    except subprocess.CalledProcessError:
      error("Failed to connect to Plaid. Make sure your plaid credentials are correct.")
    response_json = json.loads(response)
    if not response_json.has_key("access_token"):
      error("Plaid connection response did not provide an access token.")
    access_token = response_json["access_token"]
    with open("config", "a") as configfile:
      configfile.write("\n# Access token generated from Plaid\n")
      configfile.write("plaid_access_token: " + access_token + "\n")
    log("Created Plaid user.")
  else:
    error("Please provide an access token in the config file (access_token: [token]).")

# Create the cronjob file
now = datetime.now().strftime('%Y-%m-%d@%H:%M:%S')
cronjob = "/tmp/cronjob-finances-" + now
croncontents = "0 * * * * " + path + "fetch.py " + path + " 2>&1 /dev/null\n\n"
with open(cronjob, "w") as cronfile:
  cronfile.write(croncontents)
log("Cronjob file created.")

# Install the cron job
if confirm("Would you like the cron job to be automatically installed? This will clear existing jobs. If you have existing jobs, you can install it manually."):
  subprocess.call(["crontab", cronjob])
  log("Cronjob installed.")
else:
  log("Please install the following cron job with `crontab -e`: \n" + "# BEGIN CRON JOB\n" + croncontents + "# END CRON JOB")

# Copy the fetch script to install location
subprocess.call(["cp", "fetch.py", path + "fetch.py"])

# Give the fetch script execute permissions
subprocess.call(["chmod", "+x", path + "fetch.py"])
log("Fetch script installed.")

# Ensure we can reach mysql
try:
  test = mysql(config, "show databases;")
  log("Testing mysql connection with `" + " ".join(test) + "`.")
  subprocess.check_output(test)
except subprocess.CalledProcessError:
  error("Could not connect to mysql. Ensure that mysql is running.")
log("Mysql connection verified.")

# Ensure database exists, maybe create it.
database = config.get("mysql_database", "finances")
database = "asdffasdf"
check_schemas = False
try:
  test = mysql(config, "use " + database)
  log("Checking if database `" + database + "` exists.")
  subprocess.check_output(test)
  # Database exists, confirm schemas are correct
  check_schemas = True
except subprocess.CalledProcessError:
  if confirm("Database does not exist. Create it?"):
    try:
      # Create database
      command = mysql(config, "create database " + database + ";")
      log("Creating database `" + database + "` with command: `" + " ".join(command) + "`")
      subprocess.check_output(command)

      # Create accounts table
      command = mysql(config, "use " + database + """; CREATE TABLE `accounts` (
        `id` int(11) NOT NULL AUTO_INCREMENT,
        `plaid_id` varchar(64) DEFAULT NULL,
        `user` varchar(64) DEFAULT NULL,
        `available_balance` float DEFAULT NULL,
        `current_balance` float DEFAULT NULL,
        `institution_type` varchar(64) DEFAULT NULL,
        `name` varchar(64) DEFAULT NULL,
        `number` int(11) DEFAULT NULL,
        `subtype` varchar(64) DEFAULT NULL,
        `type` varchar(64) DEFAULT NULL,
        `item` varchar(64) DEFAULT NULL,
        PRIMARY KEY (`id`)
      ) ENGINE=InnoDB AUTO_INCREMENT=103 DEFAULT CHARSET=utf8""")
      log("Creating accounts table `" + database + "` with command: `" + " ".join(command) + "`")
      subprocess.check_output(command)

      # Create transactions table
      command = mysql(config, "use " + database + """; CREATE TABLE `transactions` (
        `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
        `posted` date DEFAULT NULL,
        `reference_number` text,
        `payee` varchar(512) DEFAULT NULL,
        `amount` float DEFAULT NULL,
        `category` text,
        `keywords` text,
        `pending` tinyint(1) DEFAULT '0',
        `plaid_id` varchar(64) DEFAULT NULL,
        `plaid_account_id` varchar(64) DEFAULT NULL,
        PRIMARY KEY (`id`)
      ) ENGINE=InnoDB AUTO_INCREMENT=19533 DEFAULT CHARSET=utf8""")
      log("Creating accounts table `" + database + "` with command: `" + " ".join(command) + "`")
      subprocess.check_output(command)
    except subprocess.CalledProcessError:
      error("There was a problem creating the database.")
  else:
    error("Please create database `" + database + "`.")

# Check database schemas
if check_schemas:
  try:
    # Check if accounts table is correct
    command = mysql(config, "use " + database + "; describe accounts")
    log("Checking accounts table with command: `" + " ".join(command) + "`")
    accounts_schema = subprocess.check_output(command)

    # Check if transactions table is correct
    command = mysql(config, "use " + database + "; describe transactions")
    log("Checking transactions table with command: `" + " ".join(command) + "`")
    transactions_schema = subprocess.check_output(command)

    expected_accounts_schema = """
Field Type  Null  Key Default Extra
id  int(11) NO  PRI NULL  auto_increment
plaid_id  varchar(64) YES   NULL
user  varchar(64) YES   NULL
available_balance float YES   NULL
current_balance float YES   NULL
institution_type  varchar(64) YES   NULL
name  varchar(64) YES   NULL
number  int(11) YES   NULL
subtype varchar(64) YES   NULL
type  varchar(64) YES   NULL
item  varchar(64) YES   NULL
    """

    expected_transactions_schema = """
Field Type  Null  Key Default Extra
id  int(10) unsigned  NO  PRI NULL  auto_increment
posted  date  YES   NULL
reference_number  text  YES   NULL
payee varchar(512)  YES   NULL
amount  float YES   NULL
category  text  YES   NULL
keywords  text  YES   NULL
pending tinyint(1)  YES   0
plaid_id  varchar(64) YES   NULL
plaid_account_id  varchar(64) YES   NULL
    """

    if (re.sub(r"\s+", '-', accounts_schema.strip()) != re.sub(r"\s+", '-', expected_accounts_schema.strip()) or
      re.sub(r"\s+", '-', transactions_schema.strip()) != re.sub(r"\s+", '-', expected_transactions_schema.strip())):
      if not confirm("Your table schemas do not match the expected ones. Do you wish to continue anyway?"):
        exit()
    else:
      log("Table schemas verified.")
  except subprocess.CalledProcessError:
    error("There was a problem verifying the table schemas.")

# Copy config file to path
subprocess.call(["cp", "config", path + "config"])

# Ensure that the fetch script runs by executing it once
log("Running fetch script.")
try:
  print subprocess.check_output([path + "fetch.py", path])
except subprocess.CalledProcessError:
  error("Fetch script failed to run. Make sure dependencies are installed properly.")
log("Fetch script succeeded.")
