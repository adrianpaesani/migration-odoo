# -*- coding: utf-8 -*-
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import csv


def s(txt,lg=0):
    if lg>0:
        txt=(str(txt)+u'                                                                                                 ')[:lg]
    return txt


def GetCR(db):
    try:
        cnx = psycopg2.connect("dbname='"+db+"'")
    except:
        print("Connexion à la base "+db+" impossible !")
        sys.exit()
    cr = cnx.cursor(cursor_factory=RealDictCursor)
    return cnx,cr


def CountRow(cursor,table):
    SQL="""
        SELECT count(*) as ct
        FROM """+table+"""
    """
    cursor.execute(SQL)
    rows2 = cursor.fetchall()
    nb=0
    for row2 in rows2:
        nb=row2['ct']
    return nb


def ListeTables(cr):
    SQL="""
        SELECT tablename
        FROM pg_catalog.pg_tables
        WHERE schemaname != 'pg_catalog'AND schemaname != 'information_schema'
        ORDER BY tablename
    """
    cr.execute(SQL)
    rows = cr.fetchall()
    res=[]
    for row in rows:
        res.append(row['tablename'])
    return res


def GetChamps(cursor,table):
    SQL="""
        SELECT
            a.attname
        FROM
            pg_catalog.pg_attribute a
        WHERE
            a.attrelid = (
                SELECT oid
                FROM pg_catalog.pg_class
                WHERE relname='"""+table+"""' AND relnamespace = (
                    SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'public'
                )
            )
            AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attname
    """
    cursor.execute(SQL)
    rows = cursor.fetchall()
    res=[]
    for row in rows:
        res.append(row['attname'])
    return res


def GetDistinctVal(cursor,table,champ):
    SQL="select distinct "+champ+" from "+table
    cursor.execute(SQL)
    rows = cursor.fetchall()
    return len(rows)


def GetChampsTable(cursor,table,champ=False):
    SQL="""
        SELECT
            a.attname,
            pg_catalog.format_type(a.atttypid, a.atttypmod) as type,
            a.attnotnull, a.atthasdef, adef.adsrc,
            pg_catalog.col_description(a.attrelid, a.attnum) AS comment
        FROM
            pg_catalog.pg_attribute a
            LEFT JOIN pg_catalog.pg_attrdef adef ON a.attrelid=adef.adrelid AND a.attnum=adef.adnum
        WHERE
            a.attrelid = (
                SELECT oid
                FROM pg_catalog.pg_class
                WHERE relname='"""+table+"""' AND relnamespace = (
                    SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'public'
                )
            )
            AND a.attnum > 0 AND NOT a.attisdropped
    """
    if champ:
        SQL+=" AND a.attname='"""+champ+"""' """
    SQL+="""
        ORDER BY a.attname
    """
    cursor.execute(SQL)
    rows = cursor.fetchall()
    res=[]
    for row in rows:
        nb = GetDistinctVal(cursor,table,row['attname'])
        res.append([row['attname'],row['type'], nb])
    return res


def GetModules(cursor):
    SQL="SELECT name FROM ir_module_module"
    cursor.execute(SQL)
    rows = cursor.fetchall()
    res=[]
    for row in rows:
        res.append(row['name'])
    return res


def GetGroups(cursor):
    SQL="SELECT name FROM res_groups"
    cursor.execute(SQL)
    rows = cursor.fetchall()
    res=[]
    for row in rows:
        res.append(row['name'])
    return res


def GetInfosModule(cursor,module):
    SQL="SELECT id,state FROM ir_module_module WHERE name='"+module+"'"
    cursor.execute(SQL)
    rows = cursor.fetchall()
    res=[]
    for row in rows:
        res=row
    return res


def NbChampsTable(cursor,table):
    SQL="""
        SELECT
            a.attname,
            pg_catalog.format_type(a.atttypid, a.atttypmod) as type,
            a.attnotnull, a.atthasdef, adef.adsrc,
            pg_catalog.col_description(a.attrelid, a.attnum) AS comment
        FROM
            pg_catalog.pg_attribute a
            LEFT JOIN pg_catalog.pg_attrdef adef ON a.attrelid=adef.adrelid AND a.attnum=adef.adnum
        WHERE
            a.attrelid = (
                SELECT oid
                FROM pg_catalog.pg_class
                WHERE relname='"""+table+"""' AND relnamespace = (
                    SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'public'
                )
            )
            AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attname
    """
    cursor.execute(SQL)
    rows = cursor.fetchall()
    nb=len(rows)
    return nb


def Table2CSV(cursor,table,champs='*',rename=False, default={}):
    path = "/tmp/"+table+".csv"
    if rename or default:
        SQL="SELECT "+champs+" FROM "+table
        cursor.execute(SQL)
        rows = cursor.fetchall()
        keys1 = []
        keys2 = []
        for row in rows:
            for k in row:
                x=k
                keys1.append(x)
                if k in rename:
                    x=rename[k]
                keys2.append(x)
            break
        for x in default:
            if x not in keys1:
                keys1.append(x)
            if x not in keys2:
                keys2.append(x)
        f = open(path, 'w', newline ='')
        writer = csv.DictWriter(f, fieldnames=keys1)
        f.write(','.join(keys2)+'\r\n')
        for row in rows:
            for x in default:
                row[x] = default[x]
            writer.writerow(row)
    if not rename and not default:
        #Source : https://kb.objectrocket.com/postgresql/from-postgres-to-csv-with-python-910
        SQL="SELECT "+champs+" FROM "+table
        SQL_for_file_output = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(SQL)
        with open(path, 'w') as f_output:
            cursor.copy_expert(SQL_for_file_output, f_output)


def CSV2Table(cnx_dst,cr_dst,table_src,table_dst=False):
    #Source : https://www.postgresqltutorial.com/import-csv-file-into-posgresql-table/
    if not table_dst:
        table_dst=table_src
    path = "/tmp/"+table_src+".csv"
    f = open(path, "r")
    champs = f.readline()
    SQL="""
        ALTER TABLE """+table_dst+""" DISABLE TRIGGER ALL;
        DELETE FROM """+table_dst+""";
        COPY """+table_dst+""" ("""+champs+""") FROM '/tmp/"""+table_src+""".csv' DELIMITER ',' CSV HEADER;
        ALTER TABLE """+table_dst+""" ENABLE TRIGGER ALL;
    """
    cr_dst.execute(SQL)
    cnx_dst.commit()


def SetSequence(cr_dst,cnx_dst,table):
    try:
        sequence=1
        SQL="select id from "+table+" order by id desc limit 1"
        cr_dst.execute(SQL)
        rows = cr_dst.fetchall()
        for row in rows:
            sequence=row['id']+1
        SQL="select setval('"+table+"_id_seq',"+str(sequence)+")"
        cr_dst.execute(SQL)
        cnx_dst.commit()
    except:
        pass


def MigrationTable(db_src,db_dst,table_src,table_dst=False,rename={},default={}):
    cnx_src,cr_src=GetCR(db_src)
    cnx_dst,cr_dst=GetCR(db_dst)
    if not table_dst:
        table_dst=table_src
    champs_src = GetChamps(cr_src,table_src)
    champs_dst = GetChamps(cr_dst,table_dst)
    champs = champs_src + champs_dst # Concatener les 2 listes
    for k in rename:
        champs_src.append(k)
        champs_dst.append(k)
    champs = list(set(champs))       # Supprimer les doublons
    champs.sort()                    # Trier
    communs=[]
    for champ in champs:
        if champ in champs_src and champ in champs_dst:
            communs.append(champ)
    champs=','.join(communs)
    Table2CSV(cr_src,table_src,champs,rename=rename,default=default)
    CSV2Table(cnx_dst,cr_dst,table_src,table_dst)
    SetSequence(cr_dst,cnx_dst,table_dst)


def GetChampsCommuns(cr_src,cr_dst,table):
    """Retourne la liste des champs communs aux 2 tables"""
    champs_src = GetChamps(cr_src,table)
    champs_dst = GetChamps(cr_dst,table)
    champs = champs_src + champs_dst # Concatener les 2 listes
    champs = list(set(champs))       # Supprimer les doublons
    champs.sort()                    # Trier
    communs=[]
    for champ in champs:
        if champ in champs_src and champ in champs_dst:
            communs.append(champ)
    return(communs)


def MigrationDonneesTable(db_src,db_dst,table):
    cnx_src,cr_src=GetCR(db_src)
    cnx_dst,cr_dst=GetCR(db_dst)
    champs = GetChampsCommuns(cr_src,cr_dst,table)
    for champ in champs:
        SQL="SELECT id,"+champ+" FROM "+table
        cr_src.execute(SQL)
        rows = cr_src.fetchall()
        for row in rows:
            v = row[champ]
            SQL=False
            if v:
                if type(v) is int or type(v) is float:
                    SQL="UPDATE "+table+" SET "+champ+"="+str(v)+" WHERE id="+str(row['id'])
                if type(v) is str:
                    SQL="UPDATE "+table+" SET "+champ+"='"+v+"' WHERE id="+str(row['id'])
            if SQL:
                cr_dst.execute(SQL)
    cnx_dst.commit()


def GroupName2Id(cr,name):
    SQL="select id from res_groups where name='"+name+"' limit 1"
    cr.execute(SQL)
    rows = cr.fetchall()
    id=0
    for row in rows:
        id=row['id']
    return id


def MigrationResGroups(db_src,db_dst):
    """Migration des groupes par utilisateur en se basant sur le nom du groupe"""
    cnx_src,cr_src=GetCR(db_src)
    cnx_dst,cr_dst=GetCR(db_dst)
    SQL="""
        select r.gid,r.uid,g.name
        from res_groups_users_rel r inner join res_groups g on g.id=r.gid
    """
    cr_src.execute(SQL)
    rows = cr_src.fetchall()
    for row in rows:
        name = row['name']
        uid  = row['uid']
        gid=GroupName2Id(cr_dst,name)
        if gid:
            SQL="""
                INSERT INTO res_groups_users_rel (gid, uid)
                VALUES ("""+str(gid)+""","""+str(uid)+""")
                ON CONFLICT DO NOTHING
            """
            cr_dst.execute(SQL)
    cnx_dst.commit()



def GetFielsdId(cr,model,field):
    SQL="""
        select  id,name,model
        from ir_model_fields
        where model='"""+model+"""' and name='"""+field+"""'
    """
    cr.execute(SQL)
    rows = cr.fetchall()
    fields_id=0
    for row in rows:
        fields_id=row['id']
    return fields_id


def GetCountrySrc2Dst(cr_src,cr_dst):
    """Correspondance entre les id src et dst de res_country"""
    SQL="""
        SELECT id,name
        FROM res_country
        ORDER BY name
    """
    CountrySrc2Dst={}
    cr_src.execute(SQL)
    rows = cr_src.fetchall()
    for row in rows:
        SQL="""
            SELECT id
            FROM res_country
            WHERE name=%s
        """
        cr_dst.execute(SQL,[row['name']])
        rows_dst = cr_dst.fetchall()
        for row_dst in rows_dst:
            CountrySrc2Dst[row['id']]=row_dst['id']
    return CountrySrc2Dst


def MigrationChampTable(db_src,db_dst,table,champ,ids):
    """Migration des id d'un champ d'une table à partir des ids"""
    cnx_src,cr_src=GetCR(db_src)
    cnx_dst,cr_dst=GetCR(db_dst)

    SQL="SELECT id,"+champ+" FROM "+table
    cr_dst.execute(SQL)
    rows = cr_dst.fetchall()
    for row in rows:
        id_src=row[champ]
        if id_src:
            id_dst = ids[id_src]
            SQL="UPDATE "+table+" SET "+champ+"=%s WHERE id=%s"
            cr_dst.execute(SQL,[
                    id_dst,
                    row['id'],
                ]
            )
    cnx_dst.commit()


def MigrationIrProperty(db_src,db_dst,model,field):
    """Migration des données de la table ir_property pour le model et le field indiqué"""
    cnx_src,cr_src=GetCR(db_src)
    cnx_dst,cr_dst=GetCR(db_dst)
    fields_id_src = GetFielsdId(cr_src,model,field)
    fields_id_dst = GetFielsdId(cr_dst,model,field)

    SQL="""
        DELETE FROM ir_property
        WHERE fields_id="""+str(fields_id_dst)+"""
    """
    cr_dst.execute(SQL)

    SQL="""
        select *
        from ir_property
        where fields_id="""+str(fields_id_src)+"""
        order by name,res_id
    """
    cr_src.execute(SQL)
    rows = cr_src.fetchall()
    for r in rows:
        SQL="""
            INSERT INTO ir_property (name,res_id,company_id,fields_id,value_reference,type,create_uid,create_date,write_uid,write_date)
            VALUES (
                '"""+r['name']+"""',
                '"""+str(r['res_id'])+"""',
                """+str(r['company_id'])+""",
                """+str(fields_id_dst)+""",
                '"""+r['value_reference']+"""',
                '"""+r['type']+"""',
                """+str(r['create_uid'])+""",
                '"""+str(r['create_date'])+"""',
                """+str(r['write_uid'])+""",
                '"""+str(r['write_date'])+"""'
        )"""
        cr_dst.execute(SQL)
    cnx_dst.commit()




