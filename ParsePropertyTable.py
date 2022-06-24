import re

def parseProperty(PropValue):
    # Parses the value of the "Cobol Data in USING statement" property 
    # attached to a CALL USING link or a Procedure Division
    # Output: a table with one item per Cobol Data item listed in the property
    
    PropValue=PropValue.replace('BY REFERENCE','REFERENCE')
    PropValue=PropValue.replace('BY CONTENT','CONTENT')
    PropValue=PropValue.replace('BY VALUE','VALUE')
    
    PropValueTable=PropValue.splitlines()

    line0=PropValueTable[0].strip().split()
    line0size=len(line0)
    
    if line0size < 4:
        # First item should have at least 4 elements. E.g. 1 01 M-FE REFERENCE 
        return []
    if line0[0]!='1':
        # First item should be level1. E.g. 1 01 M-FE REFERENCE 
        return []

    ParsedPropValueTable=[]
    
    for line in PropValueTable:
        line=line.strip().split()
        linelen=len(line)
        
        if line[0]=='1':
            # Level1 data item
            ParsedPropValueTable.append([line[0],line[2],'LEVEL1'])
        else:
            if linelen < 4:
                # Item should have at least 4 elements. E.g. 3 15 M-FE-NR-SECTION XXX REFERENCE
                return []
            # if line[linelen-1] not in ['REFERENCE','CONTENT','VALUE']:
            #     print ('Error: syntax problem (only BY REFERENCE, CONTENT or VALUE allowed): '+' '.join(line))
            #     return []
            
            # Groupinq data item. E.g: 2 10 M-FE-NR REFERENCE (no datatype => has sublevel(s))
            if linelen == 4:
                ParsedPropValueTable.append([line[0],line[2],'GROUP'])
                
            # Data item with type
            if linelen > 4:
                ParsedPropValueTable.append([line[0],line[2],normalizePic(line[3])])

    ParsedPropValueTableWithFullName=computeFullname(ParsedPropValueTable)
    
    return ParsedPropValueTableWithFullName

def normalizePic(pic):
    # Normalizes type description to make them comparable.
    # E.g replaces XX with X(2) or 9(05) with 9(5)...
    
    patx=re.compile('^[X]+$')
    pat9=re.compile('^[9]+$')
    
    # Strip heading '0' characters
    npic=re.sub(r'\(0+', '(', pic)
    
    if patx.match(npic):
        nb=npic.count('X')
        npic='X('+str(nb)+')'
        
    if pat9.match(npic):
        nb=npic.count('9')
        npic='9('+str(nb)+')'

    return npic     
       
       
def computeFullname(ParsedPropValueTable):
    # Computes data items fullname
    
    if ParsedPropValueTable==[]:
        print ('Parsing error:')
        print (ParsedPropValueTable)
        return []
    
    fullnameitems=[]
    curpos=0
    curlevel=1
    prevlevel=1
    prevname=''
    fnameprefixtab=[]
    
    lenParsedProperty=len(ParsedPropValueTable)
        
    while curpos < lenParsedProperty:

        prevlevel=curlevel
        
        level=ParsedPropValueTable[curpos][0]
        name=ParsedPropValueTable[curpos][1]
        pic=ParsedPropValueTable[curpos][2]
        
        curlevel=int(level)
                
        if curlevel>prevlevel and prevname!='':
            fnameprefixtab.append(prevname)
            
        if curlevel<prevlevel:
            fnameprefixtab=fnameprefixtab[:curlevel-prevlevel]
       
        fname='.'.join(fnameprefixtab)
        
        if fname=='':
            fname=name
        else:
            fname=fname+'.'+name 
              
        fullnameitems.append([level,name,pic,fname])
            
        curpos+=1        
        prevname=name
         
    return fullnameitems   


def getNoGroupItems (fullnameitems):
    # Extracts the list of level1 + actual data items (i.e not groups)
    
    lenfullnameitems=len(fullnameitems)
    curpos=0
    fullnameitemsnogroup=[]
    while curpos < lenfullnameitems:
        if fullnameitems[curpos][2]!='GROUP':
            fullnameitemsnogroup.append(fullnameitems[curpos])        
        curpos+=1
    
    return fullnameitemsnogroup


def getLevelOnePositions(ParsedProperty):
    # Produces the list of positions of Level1 items found in the input list
      
    levelonepositions=[]
    curpos=0
    propertylen=len(ParsedProperty)
    while curpos < propertylen:
        if ParsedProperty[curpos][0]=='1':
            levelonepositions.append(curpos)
        curpos+=1
    return levelonepositions


def matchProperties(idclr, idcle, PropValueClr, PropValueCle):    
    # Coordinates property matching process
    
    ParsedPropertyClr=parseProperty(PropValueClr)
    ParsedPropertyCle=parseProperty(PropValueCle)
    
    ParsedPropertyClrNoGroup=getNoGroupItems(ParsedPropertyClr)
    ParsedPropertyCleNoGroup=getNoGroupItems(ParsedPropertyCle)    
    
    if ParsedPropertyClr==[] or ParsedPropertyCle==[] or ParsedPropertyClrNoGroup==[] or ParsedPropertyCleNoGroup==[]:
        # One USING property parsing did not succeed
        return []
    
    # levelNoGroupmatch will also include level1 items:
    levelNoGroupmatch=doMatchProperties(idclr, idcle, ParsedPropertyClrNoGroup, ParsedPropertyCleNoGroup)

    return levelNoGroupmatch


def doMatchProperties(idclr, idcle, ParsedPropertyClr, ParsedPropertyCle):
    # Scans the USING property from the CALL USING Link on one side 
    # and from the called Procedure Division on the other side
    # and finds cross-matching items (data types have to match)    
    # Output: table with matching items
    
    matcheditems=[]
    
    # level1 positions tables:
    leveloneposinclr=getLevelOnePositions(ParsedPropertyClr)
    leveloneposincle=getLevelOnePositions(ParsedPropertyCle)

    # level1 positions tables length:
    leveloneposinclrlen=len(leveloneposinclr)
    leveloneposinclelen=len(leveloneposincle)    
    
    # Current position in the level1 positions tables
    curleveloneposinclr=0
    curleveloneposincle=0
    
    lenParsedPropertyClr=len(ParsedPropertyClr)
    lenParsedPropertyCle=len(ParsedPropertyCle)
    
    curposclr=0
    curposcle=0    
      
    while curleveloneposinclr < leveloneposinclrlen and curleveloneposincle < leveloneposinclelen: 
        
        curposclr=leveloneposinclr[curleveloneposinclr]
        curposcle=leveloneposincle[curleveloneposincle]

        while curposcle < lenParsedPropertyCle and curposclr < lenParsedPropertyClr :

            curpicclr=ParsedPropertyClr[curposclr][2]
            curpiccle=ParsedPropertyCle[curposcle][2]
            
            curnameclr=ParsedPropertyClr[curposclr][1]
            curnamecle=ParsedPropertyCle[curposcle][1]
            curfnameclr=ParsedPropertyClr[curposclr][3]
            curfnamecle=ParsedPropertyCle[curposcle][3]
            
            if curpicclr=='LEVEL1' or curpiccle=='LEVEL1':
                if curposclr > leveloneposinclr[curleveloneposinclr] or curposcle > leveloneposincle[curleveloneposincle]:
                    # Reached a next Level1 item 
                    break                   
                else:   
                    # Level1 matching
                    matcheditems.append([idclr,idcle,curnameclr,curnamecle,curfnameclr,curfnamecle])
                    curposclr+=1
                    curposcle+=1                    
                    continue
               
            if curpicclr==curpiccle:                    
                matcheditems.append([idclr,idcle,curnameclr,curnamecle,curfnameclr,curfnamecle])
                curposclr+=1
                curposcle+=1

            else:
                # Datatype mismatch, cannot match remaining items
                # Skipping to next parameter of the CALL USING statement (level1 items)
                # print(curnameclr+' - '+curpicclr+' ; '+curnamecle+' - '+curpiccle)
                break
                          
        curleveloneposinclr+=1 
        curleveloneposincle+=1

    return matcheditems
