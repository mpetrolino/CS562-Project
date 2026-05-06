import subprocess


def main():
    """
    This is the generator code. It should take in the MF structure and generate the code
    needed to run the query. That generated code should be saved to a 
    file (e.g. _generated.py) and then run.
    """

    body = """
    inputType = input("Enter 'txt_file' to read from file or press Enter to input values manually: ")

    if inputType == 'txt_file':
        f = open('q1.txt', 'r')
        S = f.readline().strip().split(',')
        n = int(f.readline().strip())
        V = f.readline().strip().split(',')
        F = f.readline().strip().split(',')
        sigma = f.readline().strip().split(',')
        G = f.readline().strip()
        f.close()
    else:
        print("Enter values for S, n, V, F, sigma, and G")
        S = input("Enter S (comma-separated): ").strip().split(',')
        n = int(input("Enter n (number of grouping variables): "))
        V = input("Enter V (comma-separated group-by attributes): ").strip().split(',')
        F = input("Enter F (comma-separated aggregates like sum_x,avg_y): ").strip().split(',')
        sigma = input("Enter sigma conditions (e.g. 1.state=NJ,2.city=NY): ").strip().split(',')
        G = input("Enter having clause (or leave blank): ").strip()
    
    print("S =", S)
    print("n =", n)
    print("V =", V)
    print("F =", F)
    print("sigma =", sigma)
    print("G =", G)

    def make_group_key(row, V):
        key_values = []
        for attr in V:
            key_values.append(row[attr])
        return tuple(key_values)
    
    def parse_aggregate(aggregate_name):
        #aggregate_name is broken down into grouping variable, aggregate function, and column name

        aggregate_name = aggregate_name.strip()

        first_underscore = aggregate_name.find('_')
        second_underscore = aggregate_name.find('_', first_underscore + 1)

        grouping_variable = aggregate_name[:first_underscore]
        function_name = aggregate_name[first_underscore + 1:second_underscore]
        column_name = aggregate_name[second_underscore + 1:]

        grouping_var = int(grouping_variable)
        return grouping_var, function_name, column_name

    def parse_condition(condition):
        left_side, separator, comparison_value = condition.strip().partition("=")
        grouping_variable, separator, attribute_name = left_side.partition(".")

        grouping_var = int(grouping_variable.strip())
        attribute_name = attribute_name.strip()
        comparison_value = comparison_value.strip().strip("'").strip("'")

        return grouping_var, attribute_name, comparison_value

    def matching_row(row, scan_number, sigma):
        for condition in sigma:
            condition_grouping_var, condition_attribute, condition_value = parse_condition(condition)

            if condition_grouping_var == scan_number:
                  if str(row[condition_attribute]) != condition_value:
                      return False
        
        return True

    def initialize_aggregate(function):
        match function:
            case 'sum':
                return 0
            case 'count':
                return 0
            case 'max':
                return 0
            case 'min':
                return 0
            case 'avg': 
                return 0
            case _:
                return None
    
    def update_aggregate(mf_row, aggregate, row):
        grouping_var, function, attribute = parse_aggregate(aggregate)
        row_value = row[attribute]

        
        def update_sum():
            mf_row[aggregate] += row_value

        def update_count():
            mf_row[aggregate] += 1

        def update_max():
            if mf_row[aggregate] is None:
                mf_row[aggregate] = row_value
            elif row_value > mf_row[aggregate]:
                mf_row[aggregate] = row_value

        def update_min():
            if mf_row[aggregate] is None:
                mf_row[aggregate] = row_value
            elif row_value < mf_row[aggregate]:
                mf_row[aggregate] = row_value

        def update_avg():
            sum = aggregate + '_sum'
            count = aggregate + '_count'

            mf_row[sum] += row_value
            mf_row[count] += 1
            mf_row[aggregate] += mf_row[sum] / mf_row[count]

        update_functions = {
            'sum': update_sum,
            'count': update_count,
            'max': update_max,
            'min': update_min,
            'avg': update_avg,
        }
        update_functions[function_name]()
    
    mf_struct = {}

    # Scan : 0
    def create_mf_entry(group_key):
        entry = {}

        for index, attribute_name in enumerate(V):
            entry[attribute_name] = group_key[index]
        
        for aggregate_name in F:
            grouping_var, function_name, column_name = parse_aggregate(aggregate_name)

            entry[aggregate_name] = initialize_aggregate(function_name)

            if function_name == 'avg':
                entry[aggregate_name + "_sum"] = 0
                entry[aggregate_name + "_count"] = 0
        
        return entry
    
    cur.execute("SELECT * FROM sales")

    for row in cur:
        group_key = make_group_key(row, V)

        if group_key not in mf_struct:
            mf_struct[group_key] = create_mf_entry(group_key)
    

    # Scan - 1 through n
    scan_number = 1

    while scan_number <= n:
        cur.execute("SELECT * FROM sales")

        for sales_row in cur:
            group_key = make_group_key(sales_row, V)

            if group_key in mf_struct and matching_row(sales_row, scan_number, sigma):
                for aggregate_name in F:
                    aggregate_group, function_name, column_name = parse_aggregate(aggregate_name)

                    if aggregate_group == scan_number:
                        update_aggregate(mf_struct[group_key], aggregate_name, sales_row)

        scan_number += 1

    # Output
    for key, value in mf_struct.items():
        output_row = {}

        for attribute in S:
            output_row[attribute] = value.get(attribute)

        _global.append(output_row)

      

    """

 

    # Note: The f allows formatting with variables.
    #       Also, note the indentation is preserved.
    tmp = f"""
import os
import psycopg2
import psycopg2.extras
import tabulate
from dotenv import load_dotenv

# DO NOT EDIT THIS FILE, IT IS GENERATED BY generator.py

def query():
    load_dotenv()

    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    dbname = os.getenv('DBNAME')

    conn = psycopg2.connect("dbname="+dbname+" user="+user+" password="+password,
                            cursor_factory=psycopg2.extras.DictCursor)
    cur = conn.cursor()
    cur.execute("SELECT * FROM sales")
    
    _global = []
    {body}
    
    return tabulate.tabulate(_global,
                        headers="keys", tablefmt="psql")

def main():
    print(query())
    
if "__main__" == __name__:
    main()
    """

    # Write the generated code to a file
    open("_generated.py", "w").write(tmp)
    # Execute the generated code
    subprocess.run(["python3", "_generated.py"])


if "__main__" == __name__:
    main()
