# Personal Finance Tracker
A LookML model for tracking personal finances

## Summary
This is a personal project of mine to help me track my own financial data. In this document I'll describe my process, to help you set up something similar!

## Plaid
To access my financial data from Bank of America, I use a service called [Plaid](https://plaid.com/). Plaid is an enterprise company used by companies inclidong Venmo and Acorns. They offer a free trial for up to 100 users, with unlimited access to their (testing) API. This is great news for you and me, as we are each only one user!

To get started with Plaid, head [here](https://dashboard.plaid.com/signup) and follow the directions there to sign up. You'll have to verify your email, and then you should be set up as "Pending" user (with access to the trail).

Next, try connecting a user with [this command](https://plaid.com/docs/api/#introduction):

```
curl -X POST https://tartan.plaid.com/connect \
  -d client_id=test_id \
  -d secret=test_secret \
  -d username=plaid_test \
  -d password=plaid_good \
  -d type=bofa
```

Note: I had some problems with this step. I got an error response saying I had used up all my user allowance. I contacted support and they cleared up the issue within a few hours.

Once you get an access token, move on to the install phase.

## Install Script

I wrote a little install script to ease the process of setting up a cron job that fetches your accounts and transactions. To use this, first fill out the provided config file. You'll need your plaid client id and secret from [the plaid dashboard](https://dashboard.plaid.com/#/account), your bank account login info and bank type (see [docs](https://plaid.com/docs/api/#introduction)) or the access token you received when you created the Plaid user above. You'll also need to enter an absolute path for the install location (where the intermediate csv files will be stored) and your mysql credentials. It should look something like this when you're done:

```
# plaid account information
plaid_client_id: xxxxxxx
plaid_secret: yyyyyyy
plaid_access_token: zzzzzzz

# install location
install_path: /Users/You/finances/

# these will depend on how you log into mysql
mysql_username: root
mysql_password: password

# optional, defaults to 'finances'
mysql_database: finances
```

The install script will create a database for you if you want, otherwise it will expect that the database 'finances' (or whaterver you provided for `mysql_database` in the config file) to exist and contain tables `accounts` and `transactions` with exactly these schemas:

accounts:

```
+-------------------+-------------+------+-----+---------+----------------+
| Field             | Type        | Null | Key | Default | Extra          |
+-------------------+-------------+------+-----+---------+----------------+
| id                | int(11)     | NO   | PRI | NULL    | auto_increment |
| plaid_id          | varchar(64) | YES  |     | NULL    |                |
| user              | varchar(64) | YES  |     | NULL    |                |
| available_balance | float       | YES  |     | NULL    |                |
| current_balance   | float       | YES  |     | NULL    |                |
| institution_type  | varchar(64) | YES  |     | NULL    |                |
| name              | varchar(64) | YES  |     | NULL    |                |
| number            | int(11)     | YES  |     | NULL    |                |
| subtype           | varchar(64) | YES  |     | NULL    |                |
| type              | varchar(64) | YES  |     | NULL    |                |
| item              | varchar(64) | YES  |     | NULL    |                |
+-------------------+-------------+------+-----+---------+----------------+
```

transactions:

```
+------------------+------------------+------+-----+---------+----------------+
| Field            | Type             | Null | Key | Default | Extra          |
+------------------+------------------+------+-----+---------+----------------+
| id               | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
| posted           | date             | YES  |     | NULL    |                |
| reference_number | text             | YES  |     | NULL    |                |
| payee            | varchar(512)     | YES  |     | NULL    |                |
| amount           | float            | YES  |     | NULL    |                |
| category         | text             | YES  |     | NULL    |                |
| keywords         | text             | YES  |     | NULL    |                |
| pending          | tinyint(1)       | YES  |     | 0       |                |
| plaid_id         | varchar(64)      | YES  |     | NULL    |                |
| plaid_account_id | varchar(64)      | YES  |     | NULL    |                |
+------------------+------------------+------+-----+---------+----------------+
```

Now go ahead and run the install script!

```python install.py```

## Adding Categories and Keywords

If you'd like, you can manually add categories and keywords to each of the produced transactions. Do this by editing the `transactions.csv` file that's produced. Next time the fetch script is run, these changes will be active in the database. Currently there's no way to get this data, so you'll have to do it manually for now.

## Looker

Now, start an instance of Looker, create connection to the database, then a project using that connection. Clone this repo to get the LookML files, and you should be all set to start exploring!

For in-depth documentation on Looker, see [here](https://looker.com/docs).
