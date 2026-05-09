#Mia Petrolino & Pratiksha Dadhania
#CS 562 Final Project

import subprocess
import textwrap

def main():
    body = """\
    
    #Creates generated program in _generated.py and runs code

    #Generate query input from file or inputted from user
    inputType = input("Enter 'txt_file' to read from file or press Enter to input values manually: ")

    if inputType == 'txt_file':
        f = open('q2.txt', 'r')
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

    #Create key for groups using the group by attributes (V)
    def make_group_key(row, V):
        key_values = []
        for attr in V:
            key_values.append(row[attr])
        return tuple(key_values)

    #Returns g.v. number, aggregate funct, and attribute name from "1_avg_quant"
    def parse_aggregate(aggregate_name):
        aggregate_name = aggregate_name.strip()
        first_underscore = aggregate_name.find('_')
        second_underscore = aggregate_name.find('_', first_underscore + 1)
        grouping_variable = aggregate_name[:first_underscore]
        function_name = aggregate_name[first_underscore + 1:second_underscore]
        column_name = aggregate_name[second_underscore + 1:]
        grouping_var = int(grouping_variable)
        return grouping_var, function_name, column_name

    #Returns g.v., attribute name, and comparison value from 1.state="NY"
    def parse_condition(condition):
        left_side, separator, comparison_value = condition.strip().partition("=")
        grouping_variable, separator, attribute_name = left_side.partition(".")
        grouping_var = int(grouping_variable.strip())
        attribute_name = attribute_name.strip()
        comparison_value = comparison_value.strip().strip("'").strip("'")
        return grouping_var, attribute_name, comparison_value

    #Check whether value for group satisfies the condition in sigma (and if yes will be added to the table)
    def matching_row(row, scan_number, sigma):
        for condition in sigma:
            condition_grouping_var, condition_attribute, condition_value = parse_condition(condition)
            if condition_grouping_var == scan_number:
                if str(row[condition_attribute]) != condition_value:
                    return False
        return True

    #Initializes aggregate values before computing them
    def initialize_aggregate(function):
        match function:
            case 'sum':
                return 0
            case 'count':
                return 0
            case 'max':
                return None
            case 'min':
                return None
            case 'avg':
                return 0
            case _:
                return None

    #Updates the aggregates being computed for the rows that will be added to the table
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
            #sum/count
            s = aggregate + '_sum'
            c = aggregate + '_count'
            mf_row[s] += row_value
            mf_row[c] += 1
            mf_row[aggregate] = mf_row[s] / mf_row[c]
        update_functions = {
            'sum': update_sum,
            'count': update_count,
            'max': update_max,
            'min': update_min,
            'avg': update_avg,
        }
        update_functions[function]()

    #Var (dictionary) that will be storing the results
    mf_struct = {}

    #Initializes MF structure entry for a new group
    def create_mf_entry(group_key):
        entry = {}
        #Stores grouping attribute names
        for index, attribute_name in enumerate(V):
            entry[attribute_name] = group_key[index]
        #Initializes aggregate values
        for aggregate_name in F:
            grouping_var, function_name, column_name = parse_aggregate(aggregate_name)
            entry[aggregate_name] = initialize_aggregate(function_name)
            if function_name == 'avg':
                entry[aggregate_name + "_sum"] = 0
                entry[aggregate_name + "_count"] = 0
        return entry

    cur.execute("SELECT * FROM sales")

    #Create groups (first scan)
    for row in cur:
        group_key = make_group_key(row, V)
        if group_key not in mf_struct:
            mf_struct[group_key] = create_mf_entry(group_key)

    scan_number = 1
    #Computes aggregates for g.v.s
    while scan_number <= n:
        cur.execute("SELECT * FROM sales")
        for sales_row in cur:
            group_key = make_group_key(sales_row, V)
            #Check if row belongs to group and satisfies sigma
            if group_key in mf_struct and matching_row(sales_row, scan_number, sigma):
                for aggregate_name in F:
                    aggregate_group, function_name, column_name = parse_aggregate(aggregate_name)
                    #Only update aggregates for current scan
                    if aggregate_group == scan_number:
                        update_aggregate(mf_struct[group_key], aggregate_name, sales_row)
        scan_number += 1

    #Takes care of having clause (if there)
    #If no having clause, returns True
    def evaluate_having(mf_row, G):
        if G == "":
            return True
        expression = G
        #Replace aggregate names with actual values
        for key, value in mf_row.items():
            expression = expression.replace(key, str(value))
        return eval(expression)

    #Constructs the output table
    for key, value in mf_struct.items():
        if evaluate_having(value, G):
            output_row = {}
            for attribute in S:
                output_row[attribute] = value.get(attribute)
            _global.append(output_row)
"""

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

    _global = []

{body}
    return tabulate.tabulate(_global,
                        headers="keys", tablefmt="psql")

def main():
    print(query())

if "__main__" == __name__:
    main()
"""

    open("_generated.py", "w").write(tmp)
    subprocess.run(["py", "-3.10", "_generated.py"])


if "__main__" == __name__:
    main()