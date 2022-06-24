def get_sql_create_tmp_links():
    return "create temporary table tmp_links (link_id int, idclr int, idcle int)"
def get_sql_create_using_links():
    return "create temporary table using_links (link_id int, idclr int, idcle int, dataitems text)"
def get_sql_create_using_prdiv():
    return "create temporary table using_prdiv (link_id int, idclr int, idcle int, dataitems text)"
def get_sql_create_links_table():    
    return "create temporary table create_links (idclr int, idcle int, clritem varchar(255), cleitem varchar(255), clritemfname varchar(255), cleitemfname varchar(255), clrpgmfname varchar(255), clepgmfname varchar(255), clritemid int, cleitemid int)"

def get_sql_idx_tmp_links():
    return """
    CREATE INDEX idx_tmp_links
    ON tmp_links USING btree
    (link_id ASC NULLS LAST, idclr ASC NULLS LAST, idcle ASC NULLS LAST)
    TABLESPACE pg_default
    """
def get_sql_idx_using_links():
    return """    
    CREATE INDEX idx_using_links
    ON using_links USING btree
    (link_id ASC NULLS LAST, idclr ASC NULLS LAST, idcle ASC NULLS LAST)
    TABLESPACE pg_default
    """
def get_sql_idx_using_prdiv():
    return """
    CREATE INDEX idx_using_prdiv
    ON using_prdiv USING btree
    (link_id ASC NULLS LAST, idclr ASC NULLS LAST, idcle ASC NULLS LAST)
    TABLESPACE pg_default
    """    
def get_sql_idx_create_links_idclr():
    return """
    CREATE INDEX idx_create_links_idclr
    ON create_links USING btree
    (idclr ASC NULLS LAST, idcle ASC NULLS LAST)
    TABLESPACE pg_default
    """    
def get_sql_idx_create_links_idcle():    
    return """
    CREATE INDEX idx_create_links_idcle
    ON create_links USING btree
    (idcle ASC NULLS LAST)
    TABLESPACE pg_default
    """


def get_sql_drop_tmp_links():
    return "drop table if exists tmp_links"
def get_sql_drop_using_links():
    return "drop table if exists using_links"
def get_sql_drop_using_prdiv():
    return "drop table if exists using_prdiv"
def get_sql_drop_links_table():    
    return "drop table if exists create_links"
def get_sql_drop_item_parents():    
    return "drop table if exists item_parents;"
def get_sql_drop_item_parents_final():    
    return "drop table if exists item_parents_final;"
        
def get_sql_compute_properties_step01():
    return """
        insert into tmp_links
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
        insert into using_links
        select lnk.link_id, lnk.idclr, lnk.idcle, string_agg(od.infval,E'\n' order by od.ordnum,od.blkno)
        from
        tmp_links lnk,
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
        insert into using_prdiv
        select distinct lnk.link_id, lnk.idclr, lnk.idcle, string_agg(od.infval,E'\n' order by od.ordnum,od.blkno)
        from 
        tmp_links lnk,
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
    using_links lnk,
    using_prdiv div
    where
        lnk.link_id=div.link_id
    """

def get_sql_update1_create_links_table():    
    return """
    update create_links lnk
    set 
    clrpgmfname=split_part(clr.fullname,'.',1)||'.'||split_part(clr.fullname,'.',2),
    clepgmfname=split_part(cle.fullname,'.',1)||'.'||split_part(cle.fullname,'.',2)
    from
    objfulnam clr,
    objfulnam cle
    where
        clr.idobj=lnk.idclr
    and cle.idobj=lnk.idcle
    """ 

def get_sql_update21_create_links_table():    
    return """
    update create_links lnk
    set clritemid=dat.idkey
    from 
    keys dat,
    objfulnam ofn
    where
        dat.keynam=lnk.clritem
    and dat.objtyp=831 -- Cobol Data
    and ofn.idobj=dat.idkey
    and (ofn.fullname = lnk.clrpgmfname||'.'||clritemfname
            or 
        ofn.fullname = lnk.clrpgmfname||'.LINKAGE.'||clritemfname
        )
    """
    
def get_sql_update22_create_links_table():    
    return """
    update create_links lnk
    set clritemid=dat.idkey
    from 
    keys dat,
    objfulnam ofn
    where
        clritemid is null
    and dat.keynam=lnk.clritem
    and dat.objtyp=831 -- Cobol Data
    and ofn.idobj=dat.idkey
    and (ofn.fullname like lnk.clrpgmfname||'.%.'||clritemfname escape ''
            or 
        ofn.fullname like lnk.clrpgmfname||'.%.'||clritemfname||'.%' escape ''
        )
    """    

def get_sql_update31_create_links_table():    
    return """
    update create_links lnk
    set cleitemid=dat.idkey
    from 
    keys dat,
    objfulnam ofn
    where
        dat.keynam=lnk.cleitem
    and dat.objtyp=831 -- Cobol Data
    and ofn.idobj=dat.idkey
    and (ofn.fullname = lnk.clepgmfname||'.'||cleitemfname
            or 
        ofn.fullname = lnk.clepgmfname||'.LINKAGE.'||cleitemfname
        )
    """

def get_sql_update32_create_links_table():    
    return """
    update create_links lnk
    set cleitemid=dat.idkey
    from 
    keys dat,
    objfulnam ofn
    where
        cleitemid is null
    and dat.keynam=lnk.cleitem
    and dat.objtyp=831 -- Cobol Data
    and ofn.idobj=dat.idkey
    and (ofn.fullname like lnk.clepgmfname||'.%.'||cleitemfname escape ''
            or 
        ofn.fullname like lnk.clepgmfname||'.%.'||cleitemfname||'.%' escape ''
        )
    """

def get_sql_nblinks_created():    
    return """select count(distinct (cleitemid, clritemid)) 
    from create_links
    """
