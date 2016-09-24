connection: "finances"

include: "transactions.view.lkml"
include: "keywords.view.lkml"
include: "accounts.view.lkml"

explore: transactions {
  join: keywords {
    sql_on: ${keywords.transaction_id} = ${transactions.id} ;;
    relationship: one_to_many
  }

  join: accounts {
    foreign_key: transactions.plaid_account_id
    relationship: many_to_one
  }
}

explore: accounts {}
