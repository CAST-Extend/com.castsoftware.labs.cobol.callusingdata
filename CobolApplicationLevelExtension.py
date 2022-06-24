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

class CobolApplicationLevelExtension(ApplicationLevelExtension):

    def end_application(self, application):
        
        logging.info('##################################################################')
        logging.info('Starting extension...')

        kb=application.get_knowledge_base()
        
        logging.info('Creating temporary tables...')
        kb.execute_query(sqlq.get_sql_create_tmp_links())
        kb.execute_query(sqlq.get_sql_create_using_links())
        kb.execute_query(sqlq.get_sql_create_using_prdiv())
        kb.execute_query(sqlq.get_sql_create_links_table())
        
        logging.info('SQL processing...')
        
        kb.execute_query(sqlq.get_sql_compute_properties_step01())
        kb.execute_query(sqlq.get_sql_idx_tmp_links())
        
        kb.execute_query(sqlq.get_sql_compute_properties_step02())
        kb.execute_query(sqlq.get_sql_idx_using_links())
        
        kb.execute_query(sqlq.get_sql_compute_properties_step03())
        kb.execute_query(sqlq.get_sql_idx_using_prdiv())

        logging.info('Parsing properties...')
        using_links = kb.execute_query(sqlq.get_sql_retrieve_properties())
        for row in using_links:
            #logging.info('CALLING matchedItems=parseprop.matchProperties('+str(row[0])+','+str(row[1])+','+row[2]+','+row[3])
            matchedItems=parseprop.matchProperties(row[0],row[1],row[2],row[3])
            for item in matchedItems:
                #logging.info(item)
                insert_query="insert into create_links values ("+str(item[0])+","+str(item[1])+",'"+item[2]+"','"+item[3]+"','"+item[4]+"','"+item[5]+"')"
                #logging.info(insert_query)
                kb.execute_query(insert_query)
        
        kb.execute_query(sqlq.get_sql_idx_create_links_idclr())
        kb.execute_query(sqlq.get_sql_idx_create_links_idcle())
        
        logging.info('Final SQL processing...')
        kb.execute_query(sqlq.get_sql_update1_create_links_table())
        kb.execute_query(sqlq.get_sql_update21_create_links_table())
        kb.execute_query(sqlq.get_sql_update22_create_links_table())
        kb.execute_query(sqlq.get_sql_update31_create_links_table())
        kb.execute_query(sqlq.get_sql_update32_create_links_table())

        # logging.info('Purging links...')
        # application.update_cast_knowledge_base("Delete R links between Cobol Data items", """        
        # delete from CI_NO_LINKS;        
        # insert into CI_NO_LINKS (CALLER_ID, CALLED_ID, ERROR_ID)        
        #     select idclr, idcle, 0 from Acc where acctyplo=65536 and acctyphi=0;            
        # """) 
        
        logging.info('Creating links...')
        application.update_cast_knowledge_base("Create links between Cobol Data items", """        
        delete from CI_LINKS;        
        
        insert into CI_LINKS (CALLER_ID, CALLED_ID, LINK_TYPE, ERROR_ID)        
            select distinct cleitemid, clritemid, 'referLink', 0
            from create_links
            where not exists (select 1 from acc where idclr=cleitemid and idcle=clritemid and acctyplo=65536 and acctyphi=0);            
        """) 

        nblinks_rs=kb.execute_query(sqlq.get_sql_nblinks_created())
        for row in nblinks_rs:
            nblinks=row[0]
                  
        
        logging.info('Temporary tables cleanup...')
        kb.execute_query(sqlq.get_sql_drop_tmp_links())
        kb.execute_query(sqlq.get_sql_drop_using_links())
        kb.execute_query(sqlq.get_sql_drop_using_prdiv())
        kb.execute_query(sqlq.get_sql_drop_links_table())
        kb.execute_query(sqlq.get_sql_drop_item_parents())
        kb.execute_query(sqlq.get_sql_drop_item_parents_final())
        
        logging.info('Number of links created: '+str(nblinks))
        logging.info('##################################################################')
        
