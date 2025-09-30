from prettytable import PrettyTable

if __name__ == '__main__':
    yp_table = PrettyTable()

    yp_table.field_names = (
        '№ когорты', 'Количество студентов', 'Средний балл'
    )

    yp_table.add_row([16, 200, 4.5])
    yp_table.add_row((17, 155, 4.7))
    yp_table.add_rows(
        (
            (18, 211, 4.3),
            (19, 300, 5.0),
            (13, 270, 4.1)
        )
    )
    print(yp_table)
