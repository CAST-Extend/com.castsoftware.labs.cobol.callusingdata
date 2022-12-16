def get_sql_create_all_tables():
    return """
    drop table IF EXISTS ccuext_tmp_links;
    drop table IF EXISTS ccuext_using_links;
    drop table IF EXISTS ccuext_using_prdiv;
    drop table IF EXISTS ccuext_create_links;
    create UNLOGGED table ccuext_tmp_links (link_id int, idclr int, idcle int);
    create UNLOGGED table ccuext_using_links (link_id int, idclr int, idcle int, dataitems text);
    create UNLOGGED table ccuext_using_prdiv (link_id int, idclr int, idcle int, dataitems text);
    create UNLOGGED table ccuext_create_links (idclr int, idcle int, clritem varchar(255), cleitem varchar(255), clritemfname varchar(255), cleitemfname varchar(255), clrpgmfname varchar(255), clepgmfname varchar(255), clritemid int, cleitemid int, clrfname1 varchar(255) null,clrfname2 varchar(255) null,clefname1 varchar(255) null,clefname2 varchar(255) null);
    """


def get_sql_idx_tmp_links():
    return """
    CREATE INDEX idx_tmp_links
    ON ccuext_tmp_links USING btree
    (link_id ASC NULLS LAST, idclr ASC NULLS LAST, idcle ASC NULLS LAST)
    TABLESPACE pg_default
    """    
    
def get_sql_idx_using_links():
    return """    
    CREATE INDEX idx_using_links
    ON ccuext_using_links USING btree
    (link_id ASC NULLS LAST, idclr ASC NULLS LAST, idcle ASC NULLS LAST)
    TABLESPACE pg_default
    """    
    
def get_sql_idx_using_prdiv():
    return """
    CREATE INDEX idx_using_prdiv
    ON ccuext_using_prdiv USING btree
    (link_id ASC NULLS LAST, idclr ASC NULLS LAST, idcle ASC NULLS LAST)
    TABLESPACE pg_default
    """  
      
def get_sql_idx_create_links_idclr():
    return """
    CREATE INDEX idx_create_links_idclr
    ON ccuext_create_links USING btree
    (idclr ASC NULLS LAST, idcle ASC NULLS LAST)
    TABLESPACE pg_default
    """       
    
def get_sql_idx_create_links_idcle():    
    return """
    CREATE INDEX idx_create_links_idcle
    ON ccuext_create_links USING btree
    (idcle ASC NULLS LAST)
    TABLESPACE pg_default
    """
    
def get_sql_idx_create_links_clrpgmfname():    
    return """
    CREATE INDEX idx_create_links_clrpgmfname
    ON ccuext_create_links USING btree
    (clrpgmfname ASC NULLS LAST)
    TABLESPACE pg_default;
    """    
def get_sql_idx_create_links_clepgmfname():    
    return """
    CREATE INDEX idx_create_links_clepgmfname
    ON ccuext_create_links USING btree
    (clepgmfname ASC NULLS LAST)
    TABLESPACE pg_default;  
    """
def get_sql_idx_create_links_cleitemidclritemid():    
    return """
    CREATE INDEX idx_create_links_cleitemidclritemid
    ON ccuext_create_links USING btree
    (cleitemid ASC NULLS LAST, clritemid ASC NULLS LAST)
    TABLESPACE pg_default;  
    """          
        
def get_sql_compute_properties_step01():
    return """
        insert into ccuext_tmp_links
        select lnk.link_id, lnk.caller_id, lnk.called_id
        from 
        ctv_links lnk,
        keys clr,
        keys cle
        where 
            clr.objtyp=606 --'Cobol Paragraph'
        and cle.objtyp=545 --'Cobol Program' 
        and lnk.caller_id=clr.idkey
        and lnk.called_id=cle.idkey
        and lnk.link_type_lo=2048 and lnk.link_type_hi=65536 -- Cp links
     """  
     
def get_sql_compute_properties_step02():
    return """
        insert into ccuext_using_links
        select lnk.link_id, lnk.idclr, lnk.idcle, string_agg(od.infval,E'\n' order by od.ordnum,od.blkno)
        from
        ccuext_tmp_links lnk,
        fusacc fcc,
        objdsc od
        where 
            lnk.link_id=fcc.idacc and fcc.idfus=od.idobj
        and od.InfTyp = 14000 -- Property:
        and od.InfSubTyp = 90 -- Cobol Data in USING statement
        and not od.infval  ~ '^[0-9]+[ ]+88[ ]+'  -- Exclude level 88 items
        group by lnk.link_id, lnk.idclr, lnk.idcle
    """
   
def get_sql_compute_properties_step03():
    return """
        insert into ccuext_using_prdiv
        select distinct lnk.link_id, lnk.idclr, lnk.idcle, string_agg(od.infval,E'\n' order by od.ordnum,od.blkno)
        from 
        ccuext_tmp_links lnk,
        ctt_object_parents par,
        cdt_objects prodiv,
        objdsc od
        where 
            lnk.idcle = par.parent_id
        and par.object_id = prodiv.object_id
        and par.application_type=543 --Cobol Project
        and prodiv.object_type_str='Cobol Division'
        and prodiv.object_name='Procedure Division'
        and prodiv.object_id=od.idobj
        and od.InfTyp = 14000 -- Property:
        and od.InfSubTyp = 90 -- Cobol Data in USING statement
        and not od.infval  ~ '^[0-9]+[ ]+88[ ]+' -- Exclude level 88 items
        group by lnk.link_id, lnk.idclr, lnk.idcle
    """
        
def get_sql_retrieve_properties():
    return """
    select lnk.idclr, lnk.idcle, lnk.dataitems, div.dataitems
    from 
    ccuext_using_links lnk,
    ccuext_using_prdiv div
    where
        lnk.link_id=div.link_id
    """
def get_sql_retrieve_properties_count():    
    return """select count(distinct(lnk.idclr, lnk.idcle, lnk.dataitems, div.dataitems)) 
    from 
    ccuext_using_links lnk,
    ccuext_using_prdiv div
    where
        lnk.link_id=div.link_id
    """    

def get_sql_update1_create_links_table():    
    return """
    update ccuext_create_links lnk
    set 
    clrpgmfname=split_part(clr.fullname,'.',1)||'.'||split_part(clr.fullname,'.',2),
    clepgmfname=split_part(cle.fullname,'.',1)||'.'||split_part(cle.fullname,'.',2),
    clrfname1=substring(split_part(clr.fullname,'.',1)||'.'||split_part(clr.fullname,'.',2)||'.'||clritemfname,1,255),
    clrfname2=substring(split_part(clr.fullname,'.',1)||'.'||split_part(clr.fullname,'.',2)||'.LINKAGE.'||clritemfname,1,255),
    clefname1=substring(split_part(cle.fullname,'.',1)||'.'||split_part(cle.fullname,'.',2)||'.'||cleitemfname,1,255),
    clefname2=substring(split_part(cle.fullname,'.',1)||'.'||split_part(cle.fullname,'.',2)||'.LINKAGE.'||cleitemfname,1,255)    
    from
    objfulnam clr,
    objfulnam cle
    where
        lnk.idclr=clr.idobj
    and lnk.idcle=cle.idobj
    """ 

def get_sql_update21_create_links_table():    
    return """
    update ccuext_create_links lnk
    set clritemid=ofn.object_id
    from 
    cdt_objects ofn
    where
        lnk.clritemid=0
    and ofn.object_name=lnk.clritem
    and ofn.object_type_str='Cobol Data'
    and (ofn.object_fullname = lnk.clrfname1
            or 
        ofn.object_fullname = lnk.clrfname2
        )
    """
    
def get_sql_update22_create_links_table():
    # Data item passed is not level 1    
    return """
    update ccuext_create_links lnk
    set clritemid=ofn.object_id
    from 
    cdt_objects ofn
    where
        lnk.clritemid=0
    and ofn.object_name=lnk.clritem
    and ofn.object_type_str='Cobol Data'
    and ofn.object_fullname like substring(lnk.clrpgmfname||'.%.'||lnk.clritemfname,1,254)||'%' escape ''
    """  
def get_sql_update23_create_links_table():
    # Data item passed is not level 1 and full name is truncated    
    return """
    update ccuext_create_links lnk
    set clritemid=ofn.object_id
    from 
    cdt_objects ofn
    where
        lnk.clritemid=0
    and ofn.object_name=lnk.clritem
    and ofn.object_type_str='Cobol Data'
    and ofn.object_fullname like substring(lnk.clrpgmfname||'.%.'||lnk.clritemfname,1,204)||'%' escape ''
    """    

def get_sql_update31_create_links_table():    
    return """
    update ccuext_create_links lnk
    set cleitemid=ofn.object_id
    from 
    cdt_objects ofn
    where
        lnk.cleitemid=0
    and ofn.object_name=lnk.cleitem
    and ofn.object_type_str='Cobol Data'
    and (ofn.object_fullname = lnk.clefname1
            or 
        ofn.object_fullname = lnk.clefname2
        )
    """

def get_sql_update32_create_links_table():
    # Data item passed is not level 1     
    return """
    update ccuext_create_links lnk
    set cleitemid=ofn.object_id
    from 
    cdt_objects ofn
    where
        lnk.cleitemid=0
    and ofn.object_name=lnk.cleitem
    and ofn.object_type_str='Cobol Data'
    and ofn.object_fullname like substring(lnk.clepgmfname||'.%.'||lnk.cleitemfname,1,254)||'%' escape ''
    """

def get_sql_update33_create_links_table():
    # Data item passed is not level 1 and full name is truncated (unlikely)  
    return """
    update ccuext_create_links lnk
    set cleitemid=ofn.object_id
    from 
    cdt_objects ofn
    where
        lnk.cleitemid=0
    and ofn.object_name=lnk.cleitem
    and ofn.object_type_str='Cobol Data'
    and ofn.object_fullname like substring(lnk.clepgmfname||'.%.'||lnk.cleitemfname,1,204)||'%' escape ''
    """

def get_sql_nblinks_created():    
    return """select count(distinct (cleitemid, clritemid)) 
    from ccuext_create_links
    where clritemid != 0 and cleitemid != 0
    """

