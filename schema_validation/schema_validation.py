import pandas as pd
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader
import os
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import argparse
from argparse import RawTextHelpFormatter

csv_path = r"schemacomparesql.csv"
output_directory_path = r"schema_validation"
merged_summary = pd.DataFrame()

def load_environment(): 
    env = Environment(loader=FileSystemLoader(''))
    template = env.get_template('sample_report_template.html')
    return template

def connection(args):
    oracle_alchemy_connection = f"oracle+cx_oracle://{args.ora_connection}"
    postgres_alchemy_connection = f"postgresql+psycopg2://{args.pg_connection}"

    engine_oracle = create_engine(oracle_alchemy_connection)
    conn_oracle = engine_oracle.connect()

    engine_postgres = create_engine(postgres_alchemy_connection)
    conn_postgres =engine_postgres.connect()
    return conn_oracle, conn_postgres

def command_args():
    parser = argparse.ArgumentParser(description='Oracle-PostgreSQL Conversion Validator \n Sample command to run Conversion Validator \n python schema_validation.py --ora-connection <<username>>:<<password>>@<<HostName>>:<<Port>>/?service_name=<<DBName>> --pg-connection <<username>>:<<password>>@<<HostName>>:<<Port>>/<<DBName>> --ora-schema <<schema_name>> --pg-schema <<schema_name>>' , formatter_class=RawTextHelpFormatter)
    parser.add_argument('--ora-connection', required=True, help='Oracle Connection(<<username>>:<<password>>@<<HostName>>:<<Port>>/?service_name=<<DBName>>)')
    parser.add_argument('--pg-connection', required=True, help='PostgreSQL Connection (<<username>>:<<password>>@<<HostName>>:<<Port>>/<<DBName>>)')
    parser.add_argument('--ora-schema', required=True, help='Oracle Schema name')
    parser.add_argument('--pg-schema', required=True, help='PostgreSQL Schema name')
    # parser.add_argument('-v', required=False, help='Enable logging all queries to console')
    parser.add_argument('-v', '--verbose',action='store_true')

    args = parser.parse_args()
    return args

def read_csv (conn_oracle, conn_postgres, args):
    # csv_path = r"schemacomparesql.csv"
    data = pd.read_csv(csv_path)
    desired_join = "outer"
    valid_joins = ["right", "left", "outer", "inner"]
    if desired_join not in valid_joins:
        print("Invalid input. Applying default outer join")
        desired_join = "outer"    

    missing_rows = {}
    section_titles =  {}
    descriptions = {}
    missing_rows_index = 1

    for index,row in data.iterrows():
        oracle_query = row["oracle_sql"]
        postgres_query = row["postgresql_sql"]
        ref_col = list(row['refcol'].split(","))
        desired_missing_data = row['dbtovalidate']  
        section_title = row["module"]
        description = row["description"]

        replaced_value1 = oracle_query.replace("<<ORACLE_SCHEMA_NAME>>", args.ora_schema.upper())
        #print(Oracle - replaced_value1)
        replaced_value2 = postgres_query.replace("<<POSTGRES_SCHEMA_NAME>>", args.pg_schema.lower())
        #print(PostgreSQL - replaced_value2)

        if args.verbose :
            print(replaced_value1,replaced_value2)

        ora_name = args.ora_schema
        
        df1 = pd.read_sql_query(replaced_value1, conn_oracle )
        df2 = pd.read_sql_query(replaced_value2, conn_postgres)
        
        # df1.columns = df1.columns.str.upper()
        # df2.columns = df2.columns.str.upper()

        merged_df = df1.merge(df2, on=ref_col, sort=True, how=desired_join, indicator="ind", suffixes=('_oracle', '_postgres'))
        for f in merged_df.columns:
            if merged_df[f].dtype == "object":
                merged_df[f] = merged_df[f].fillna("")
                
        if desired_missing_data == "postgres":
            # missing_rows[missing_rows_index] = merged_df[merged_df['ind'] == "left_only"].loc[:, merged_df.columns != "ind"]
            # missing_rows[missing_rows_index] = merged_df.loc[:, ~merged_df.columns.str.endswith("_postgres")]
            missing_rows[missing_rows_index] = merged_df[merged_df['ind'] == "left_only"].loc[:, ~merged_df.columns.isin(["ind"]) & ~merged_df.columns.str.endswith('_postgres')]
            section_titles[missing_rows_index] = section_title
            descriptions[missing_rows_index] = description
            missing_rows_index=missing_rows_index+1
        elif desired_missing_data == "oracle":
            missing_rows[missing_rows_index] = merged_df[merged_df['ind'] == "right_only"].loc[:, ~merged_df.columns.isin(["ind"]) & ~merged_df.columns.str.endswith('_oracle')]
            section_titles[missing_rows_index] = section_title
            descriptions[missing_rows_index] = description
            missing_rows_index=missing_rows_index+1
        elif desired_missing_data == "both":
            missing_rows[missing_rows_index] = merged_df[merged_df['ind'] == "both"].loc[:, merged_df.columns != "ind"]
            section_titles[missing_rows_index] = section_title
            descriptions[missing_rows_index] = description
            missing_rows_index=missing_rows_index+1
        else:
            merged_summary = merged_df.loc[:, merged_df.columns != "ind"].fillna(0)
            section_titles[0] = section_title
            descriptions[0] = description
            missing_rows[0] = merged_summary

            generate_summary_chart(merged_summary,ora_name)
            

    return index, df1, df2, ref_col, desired_missing_data,desired_join,missing_rows, merged_summary, section_titles,descriptions,ora_name

def generate_summary_chart(merged_summary,ora_name):
    bar_width = 0.35
    x = merged_summary["object_type"]
    y_positions = np.arange(len(x))
    
    height_oracle = merged_summary['cnt_oracle']
    height_oracle = pd.to_numeric(merged_summary['cnt_oracle'], errors='coerce').fillna(0).astype(int)
    height_postgres = merged_summary['cnt_postgres']
    height_postgres = pd.to_numeric(merged_summary['cnt_postgres'], errors='coerce').fillna(0).astype(int)

    plt.bar(y_positions - bar_width/2, height_oracle, bar_width, label='Oracle', color='skyblue', align='center')
    plt.bar(y_positions + bar_width/2, height_postgres, bar_width, label='PostgreSQL', color='lightgrey', align='center')

    for i, (h_oracle, h_postgres) in enumerate(zip(height_oracle, height_postgres)):
        plt.annotate(str(h_oracle), (y_positions[i] - bar_width/2, h_oracle), ha='center', va='bottom', color='black')
        plt.annotate(str(h_postgres), (y_positions[i] + bar_width/2, h_postgres), ha='center', va='bottom', color='black')

    plt.xticks(y_positions, x, rotation = 45)
    plt.ylabel('Count')
    plt.xlabel('Object Type')
    plt.title('Comparison of Object between Oracle and PostgreSQL')
    # oracle = mpatches.Patch(color='skyblue', label='Oracle')
    # postgres = mpatches.Patch(color='lightcoral', label='PostgresSQL')
    plt.legend(labels = ["Oracle","PostgreSQL"])
    # plt.legend(labels = ["PostgresSQL"])
    #plt.legend().remove()
    plt.tight_layout()
    plt.gcf().set_size_inches(10, 6)
    output_directory = f'{output_directory_path}_{ora_name}'
    os.makedirs(output_directory, exist_ok=True)
    output_chart = os.path.join(output_directory, "schemareport.png")
    plt.savefig(output_chart)    
    
def generate_html(missing_rows,template,section_titles,descriptions,ora_name):
    rendered_html = template.render(missing_rows=missing_rows,section_titles=section_titles,descriptions=descriptions)
    output_directory = f'{output_directory_path}_{ora_name}'
    os.makedirs(output_directory, exist_ok=True)
    output_file = os.path.join(output_directory, f"oracle_pg_validation_{ora_name}.html")

    with open(output_file, "w") as html_file:
        html_file.write(rendered_html)

    print("HTML report generated successfully.")
    print(f"Report Generated : schema_validation\schema_validation_{ora_name}\oracle_pg_validation_{ora_name}.html")

if __name__=="__main__":

    args = command_args()
    conn_oracle, conn_postgres = connection(args)
    index, df1, df2, ref_col, desired_missing_data,desired_join,missing_rows, merged_summary,section_titles,descriptions,ora_name = read_csv (conn_oracle, conn_postgres, args)
    
    template = load_environment()
    generate_html(missing_rows,template,section_titles,descriptions,ora_name)
    conn_oracle, conn_postgres = connection(args)
    read_csv (conn_oracle, conn_postgres, args)


    











