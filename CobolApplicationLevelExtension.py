'''
Created on May 25, 2022
Creates referLink between Cobol Data items based on CALL USING statements
@author: CastLabs
'''
import ParsePropertyTable as parseprop
import SqlQueries as sqlq
import cast_upgrade_1_6_13 # @UnusedImport
import logging
from cast.application import ApplicationLevelExtension
from datetime import datetime

from cast.application import reflect_table


class CobolApplicationLevelExtension(ApplicationLevelExtension):

    def end_application(self, application):
        
        logging.info('##################################################################')
        date_start=datetime.now()
        logging.info('Starting extension...')

        kb=application.get_knowledge_base()
        
        logging.info('Creating work tables...')
        application.sql_tool(sqlq.get_sql_create_all_tables())
        
        logging.info('Populating work tables...')
        kb.execute_query(sqlq.get_sql_compute_properties_step01())
        kb.execute_query(sqlq.get_sql_idx_tmp_links())
        kb.execute_query(sqlq.get_sql_compute_properties_step02())
        kb.execute_query(sqlq.get_sql_idx_using_links())
        kb.execute_query(sqlq.get_sql_compute_properties_step03())
        kb.execute_query(sqlq.get_sql_idx_using_prdiv())
        

        logging.info('Parsing properties of CALL USING links...')
        using_links = kb.execute_query(sqlq.get_sql_retrieve_properties())

        using_links_count=kb.execute_query(sqlq.get_sql_retrieve_properties_count())
        for row in using_links_count:
            nb_using_links=str(row[0])
                    
        using_links_cpt=0
        for row in using_links:
            matchedItems=parseprop.matchProperties(row[0],row[1],row[2],row[3])
            insert_data=[]
            for item in matchedItems:
                insert_data.append((item[0],item[1],str(item[2]),str(item[3]),str(item[4]),str(item[5]),'','',0,0,'','','',''))
            insert_create_links_values(self,kb,insert_data)
            using_links_cpt+=1
            logging.info('CALL USING links parsed: '+str(using_links_cpt)+' / '+nb_using_links)
           
        logging.info('Updating work tables...')
        logging.info('Step 1/6')
        kb.execute_query(sqlq.get_sql_idx_create_links_idclr())
        kb.execute_query(sqlq.get_sql_idx_create_links_idcle())
        logging.info('Step 2/6')
        kb.execute_query(sqlq.get_sql_update1_create_links_table())
        logging.info('Step 3/6')
        kb.execute_query(sqlq.get_sql_update21_create_links_table())
        logging.info('Step 4/6')
        kb.execute_query(sqlq.get_sql_update22_create_links_table())
        kb.execute_query(sqlq.get_sql_update23_create_links_table())
        logging.info('Step 5/6')
        kb.execute_query(sqlq.get_sql_update31_create_links_table())
        logging.info('Step 6/6')
        kb.execute_query(sqlq.get_sql_update32_create_links_table())
        kb.execute_query(sqlq.get_sql_update33_create_links_table())
        kb.execute_query(sqlq.get_sql_idx_create_links_cleitemidclritemid())

        # logging.info('Purging existing Cobol data items <Refer> links...')
        # application.update_cast_knowledge_base("Deletes Refer links between Cobol data items", """        
        # delete from CI_NO_LINKS;        
        # insert into CI_NO_LINKS (CALLER_ID, CALLED_ID, ERROR_ID)        
        #     select idclr, idcle, 0 from Acc where acctyplo=65536 and acctyphi=0;            
        # """) 
        
        logging.info('Creating links...')
        application.update_cast_knowledge_base("Creating links between Cobol data items...", """        
        delete from CI_LINKS;        
        
        insert into CI_LINKS (CALLER_ID, CALLED_ID, LINK_TYPE, ERROR_ID)        
            select distinct cleitemid, clritemid, 'referLink', 0
            from ccuext_create_links
            where clritemid != 0 and cleitemid != 0
            and not exists (select 1 from acc where idclr=cleitemid and idcle=clritemid and acctyplo=65536 and acctyphi=0);            
        """) 

        nblinks_rs=kb.execute_query(sqlq.get_sql_nblinks_created())
        for row in nblinks_rs:
            nblinks=row[0]
        
        logging.info('Number of links created: '+str(nblinks))
        logging.info('Total duration: '+str(datetime.now()-date_start))
        logging.info('##################################################################')
        


def insert_create_links_values(self, kb, values):                
    # bulk insert
    create_links = reflect_table('ccuext_create_links', kb.metadata, kb.engine)
    ins = create_links.insert()
    cursor = kb.create_cursor()
    cursor.executemany(str(ins.compile()), values)
    kb.raw_connection.commit()
        
