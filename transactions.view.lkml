view: transactions {
  sql_table_name: finances.transactions ;;

  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.id ;;
    drill_fields: [detail*, -id]
  }

  dimension: amount {
    type: number
    sql: ${TABLE}.amount ;;
    html: <span style='color: {{ transactions.color }};'> {{ rendered_value }}</span> ;;
    html:
      {% if value > 0 %}
      <font color="#bb3030">{{ rendered_value }}</font>
      {% else %}
      <font color="black">{{ rendered_value }}</font>
      {% endif %} ;;
    value_format_name: usd
    drill_fields: [detail*, -amount]
  }

  dimension: category {
    type: string
    # turn blanks into nulls
    sql: CASE WHEN ${TABLE}.category IS NULL OR ${TABLE}.category = ''
              THEN 'other'
              ELSE ${TABLE}.category
         END ;;
    drill_fields: [detail*, -category]
  }

  dimension: keywords {
    type: string
    sql: ${TABLE}.keywords ;;
    drill_fields: [detail*, -keywords]
  }

  dimension_group: period {
    type: time
    timeframes: [date, week, month]
    convert_tz: no
    sql: ${TABLE}.period ;;
    drill_fields: [detail*, -period_date]
  }

  dimension_group: posted {
    type: time
    timeframes: [date, week, month, day_of_week, month_name, day_of_month]
    convert_tz: no
    sql: ${TABLE}.posted ;;
    drill_fields: [detail*, -posted_date]
  }

  dimension: reference_number {
    type: string
    sql: ${TABLE}.reference_number ;;
    drill_fields: [detail*]
  }

  dimension: plaid_account_id {
    sql: ${TABLE}.plaid_account_id ;;
  }

  # # # # # # # # # # # # # # # # # # # # # # #
  # PAYEE DIMENSIONS

  dimension: amazon {
    group_label: "Payee"
    type: yesno
    sql: payee LIKE '%amazon%' ;;
    drill_fields: [detail*]
  }

  dimension: paypal {
    group_label: "Payee"
    type: yesno
    sql: payee LIKE '%paypal%' ;;
    drill_fields: [detail*]
  }

  dimension: payee {
    group_label: "Payee"
    type: string
    sql: ${TABLE}.payee ;;
    drill_fields: [detail*, -payee]

    link: {
      label: "Google Search this Payee"
      url: "https://www.google.com/search?q={{ value || encode_uri }}"
    }
  }

#   dimension: state {
#     sql: CASE WHEN RIGHT(TRIM(${payee}), 2) IN (
#         'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
#         'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
#         'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
#         'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
#         'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY')
#       THEN RIGHT(TRIM(${payee}), 2)
#       ELSE NULL
#     END ;;
#     drill_fields: [detail*]
#   }

  # # # # # # # # # # # # # # # # # # # # # # #
  # MEASURES

  measure: count {
    # distinct because symmetric aggregates
    type: count
    drill_fields: [id]
  }

  measure: total {
    # distinct because symmetric aggregates
    type: sum
    value_format_name: usd
    html:
      {% if value > 0 %}
      <font color="#bb3030">{{ rendered_value }}</font>
      {% else %}
      <font color="black">{{ rendered_value }}</font>
      {% endif %} ;;
    sql: ${amount} ;;
  }

  measure: average {
    type: average
    value_format_name: usd
    sql: ${amount} ;;
    html:
      {% if value > 0 %}
      <font color="#bb3030">{{ rendered_value }}</font>
      {% else %}
      <font color="black">{{ rendered_value }}</font>
      {% endif %} ;;
  }

  measure: max {
    type: max
    value_format_name: usd
    sql: ${amount} ;;
    html:
      {% if value > 0 %}
      <font color="#bb3030">{{ rendered_value }}</font>
      {% else %}
      <font color="black">{{ rendered_value }}</font>
      {% endif %} ;;
  }

  set: detail {
    fields: [category, amount, keywords, period_date, posted_date, payee]
  }

}