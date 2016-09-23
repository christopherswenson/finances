view: keywords {
  derived_table: {
    # SQL magic from http://stackoverflow.com/a/19073575
    # generate list of all keywords, with primary key and transaction foreign key
    sql: SELECT
        CAST(@rownum := @rownum + 1 AS UNSIGNED) AS id,
        keywords.id AS transaction_id,
        SUBSTRING_INDEX(SUBSTRING_INDEX(keywords, ',', n.n), ',', -1) value
      FROM transactions keywords CROSS JOIN (
        SELECT a.N + b.N * 10 + 1 n
        FROM
          (SELECT 0 AS N UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) a,
          (SELECT 0 AS N UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) b
        ORDER BY n
      ) n
    WHERE n.n <= 1 + (LENGTH(keywords) - LENGTH(REPLACE(keywords, ',', '')))
    ORDER BY value ;;
  }

  dimension: id {
    type: number
    primary_key: yes
  }

  dimension: name {
    type: string
    # turn blanks into nulls
    sql: CASE WHEN ${TABLE}.value = ''
      THEN NULL
      ELSE ${TABLE}.value
    END ;;
    drill_fields: [transactions.category, transactions.total, transactions.address, transactions.payee]
  }

  dimension: transaction_id {
    type: number
  }
}
