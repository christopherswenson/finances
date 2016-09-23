view: accounts {
  sql_table_name: finances.accounts ;;

  dimension: plaid_id {
    hidden: yes
    primary_key: yes
    sql: ${TABLE}.plaid_id ;;
  }

  dimension: id {
    type: number
    sql: ${TABLE}.id  ;;
  }

  dimension: user {
    hidden: yes
    type: string
    sql: ${TABLE}.user ;;
  }

  dimension: available_balance {
    type: number
    sql: ${TABLE}.available_balance ;;
    html:
      {% if value < 0 %}
      <font color="#bb3030">{{ rendered_value }}</font>
      {% else %}
      <font color="black">{{ rendered_value }}</font>
      {% endif %} ;;
    value_format_name: usd
  }

  dimension: current_balance {
    type: number
    sql: ${TABLE}.current_balance ;;
    html:
      {% if value < 0 %}
      <font color="#bb3030">{{ rendered_value }}</font>
      {% else %}
      <font color="black">{{ rendered_value }}</font>
      {% endif %} ;;
    value_format_name: usd
  }

  dimension: institution_type {
    type: string
    sql: ${TABLE}.institution_type ;;
  }

  dimension: name {
    type: string
    sql: ${TABLE}.name ;;
  }

  dimension: number {
    type: number
    sql: ${TABLE}.number ;;
  }

  dimension: type {
    type: string
    sql: ${TABLE}.type ;;
  }


}
