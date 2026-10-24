"""Supported CAGEBOT block exporter, derived from the project v5 generator (MIT)."""
import json
import xml.etree.ElementTree as ET
NS="https://developers.google.com/blockly/xml"
ET.register_namespace("",NS)
def op(kind, a, b): return (kind, a, b)
def add(a, b): return op('ADD', a, b)
def sub(a, b): return op('MINUS', a, b)
def mul(a, b): return op('MULTIPLY', a, b)
def div(a, b): return op('DIVIDE', a, b)
def eq(a, b): return op('EQ', a, b)
def ne(a, b): return op('NEQ', a, b)
def lt(a, b): return op('LT', a, b)
def le(a, b): return op('LTE', a, b)
def gt(a, b): return op('GT', a, b)
def ge(a, b): return op('GTE', a, b)
def both(a, b): return op('AND', a, b)
def either(a, b): return op('OR', a, b)
def setv(name, value): return ('set', name, value)
def call(name): return ('call', name)
def cond(test, yes, no=None): return ('if', [(test, yes)], no)
def cases(branches, otherwise=None): return ('if', branches, otherwise)
def anyof(expr, values):
    result = eq(expr, values[0])
    for v in values[1:]: result = either(result, eq(expr, v))
    return result

class Exporter:
    def __init__(self): self.seq=0
    def elem(self,tag,**kw): return ET.Element('{'+NS+'}'+tag,kw)
    def block(self,typ):
        self.seq+=1
        return self.elem('block',type=typ,id=f'v5_{self.seq:05d}')
    def field(self,b,name,text):
        f=self.elem('field',name=name); f.text=str(text)
        if name=='VAR': f.set('id','var_'+str(text))
        b.append(f)
    def value(self,b,name,expr):
        v=self.elem('value',name=name); v.append(self.expr(expr)); b.append(v)
    def statement(self,b,name,items):
        s=self.elem('statement',name=name); chain=self.chain(items)
        if chain is not None: s.append(chain)
        b.append(s)
    def expr(self,e):
        if isinstance(e,int): b=self.block('math_number'); self.field(b,'NUM',e); return b
        if isinstance(e,str): b=self.block('variables_get'); self.field(b,'VAR',e); return b
        k=e[0]
        if k=='text': b=self.block('text'); self.field(b,'TEXT',e[1]); return b
        if k=='millis': return self.block('millis')
        if k in ('analog','digital'):
            b=self.block('inout_analog_read' if k=='analog' else 'inout_digital_read')
            self.field(b,'PIN',e[1]); return b
        typ='math_arithmetic' if k in ('ADD','MINUS','MULTIPLY','DIVIDE') else (
            'logic_operation' if k in ('AND','OR') else 'logic_compare')
        b=self.block(typ); self.field(b,'OP',k); self.value(b,'A',e[1]); self.value(b,'B',e[2]); return b
    def stmt(self,s):
        k=s[0]
        if k=='declare':
            b=self.block('variables_declare'); self.field(b,'VAR',s[1]); self.field(b,'TYPE',s[2]); self.value(b,'VALUE',s[3])
        elif k=='set':
            b=self.block('variables_set'); self.field(b,'VAR',s[1]); self.value(b,'VALUE',s[2])
        elif k=='call':
            b=self.block('procedures_callnoreturn'); m=self.elem('mutation',name=s[1]); b.append(m)
        elif k=='if':
            b=self.block('controls_if'); m=self.elem('mutation',elseif=str(len(s[1])-1))
            if s[2] is not None: m.set('else','1')
            b.append(m)
            for i,(test,body) in enumerate(s[1]): self.value(b,'IF'+str(i),test); self.statement(b,'DO'+str(i),body)
            if s[2] is not None: self.statement(b,'ELSE',s[2])
        elif k=='digitalwrite':
            b=self.block('inout_digital_write'); self.field(b,'PIN',s[1]); self.field(b,'STAT','HIGH' if s[2] else 'LOW')
        elif k=='pwm':
            b=self.block('inout_analog_write'); self.field(b,'PIN',s[1]); self.value(b,'Value',s[2])
        elif k=='serial':
            b=self.block('serial_setup'); self.field(b,'SERIAL_ID','Serial'); self.field(b,'SERIAL_SPEED',s[1])
        elif k=='print':
            b=self.block('serial_print' if s[2] else 'serial_printL'); self.value(b,'CONTENT',s[1])
        else: raise ValueError(k)
        return b
    def chain(self,items):
        head=last=None
        for s in items:
            b=self.stmt(s)
            if head is None: head=b
            else: n=self.elem('next'); n.append(b); last.append(n)
            last=b
        return head
    def xml(self,variables,funcs,setup,loop):
        root=self.elem('xml'); vs=self.elem('variables')
        for name in variables:
            v=self.elem('variable',id='var_'+name); v.text=name; vs.append(v)
        root.append(vs)
        main=self.block('arduino_setup'); main.set('x','20'); main.set('y','-1400')
        self.statement(main,'MySetup',setup); self.statement(main,'MyLoop',loop); root.append(main)
        for i,(name,body) in enumerate(funcs.items()):
            b=self.block('procedures_defnoreturn'); b.set('x',str(1200+(i%3)*700)); b.set('y',str((i//3)*600))
            self.field(b,'NAME',name); self.field(b,'TYPE','void'); self.statement(b,'STACK',body); root.append(b)
        ET.indent(root,space='  ')
        return ET.tostring(root,encoding='unicode')+'\n'


# The Arduino translator consumes the actual XML, so XML edits can also be exported.
# It deliberately rejects every unknown block rather than silently dropping logic.
def xml_to_ino(xml_text):
    root=ET.fromstring(xml_text); ns={'b':NS}
    # Older CAGEBOT mutation serializers use document.createElement(), so a saved
    # mutation/arg can carry XHTML or no namespace inside otherwise Blockly XML.
    for element in root.iter():
        local=element.tag.split('}')[-1]
        if local in ('mutation','arg') and element.tag in (
                local,'{http://www.w3.org/1999/xhtml}'+local):
            element.tag='{'+NS+'}'+local
    known={'arduino_setup','variables_declare','variables_set','variables_get',
           'math_number','math_arithmetic','logic_operation','logic_compare',
           'text','millis','inout_analog_read','inout_digital_read',
           'inout_digital_write','inout_analog_write','serial_setup','serial_print',
           'serial_printL','procedures_callnoreturn','procedures_defnoreturn','controls_if'}
    for b in root.findall('.//b:block',ns)+root.findall('.//b:shadow',ns):
        if b.get('type') not in known: raise ValueError('Unsupported block '+str(b.get('type')))
        if b.get('disabled')=='true': raise ValueError('Disabled blocks require explicit review before export')
        if b.find('b:mutation/b:arg',ns) is not None:
            raise ValueError('Procedure arguments are not supported by this translator')
    if len(root.findall("b:block[@type='arduino_setup']",ns))!=1:
        raise ValueError('Exactly one arduino_setup is required')
    if any(b.get('type') not in ('arduino_setup','procedures_defnoreturn')
           for b in root.findall('b:block',ns)):
        raise ValueError('Unconnected top-level executable block')
    fields=lambda b:{f.get('name'):f.text for f in b.findall('b:field',ns)}
    declarations={}; pinmodes={}; functions={}; serials={}
    operators={'ADD':'+','MINUS':'-','MULTIPLY':'*','DIVIDE':'/',
               'EQ':'==','NEQ':'!=','LT':'<','LTE':'<=','GT':'>','GTE':'>=',
               'AND':'&&','OR':'||'}
    def value(b,n):
        v=b.find(f"b:value[@name='{n}']",ns)
        if v is None or not len(v): raise ValueError('Missing input '+n)
        return expr(v[0])
    def statement(b,n):
        v=b.find(f"b:statement[@name='{n}']/b:block",ns)
        return chain(v) if v is not None else ''
    def expr(b):
        t=b.get('type'); f=fields(b)
        if t=='math_number':
            n=int(f['NUM']); return str(n)+'L'  # Avoid AVR 16-bit intermediate overflow.
        if t=='variables_get': return f['VAR']
        if t=='text': return json.dumps(f['TEXT'])
        if t=='millis': return 'millis()'
        if t in ('inout_analog_read','inout_digital_read'):
            pinmodes[f['PIN']]='INPUT'
            return ('analogRead' if t=='inout_analog_read' else 'digitalRead')+'('+f['PIN']+')'
        if t in ('math_arithmetic','logic_operation','logic_compare'):
            return '('+value(b,'A')+' '+operators[f['OP']]+' '+value(b,'B')+')'
        raise ValueError('Unsupported expression block '+str(t))
    def chain(b):
        result=''
        while b is not None:
            t=b.get('type'); f=fields(b)
            if t=='variables_declare':
                declarations[f['VAR']]=f['TYPE']; result+=f['VAR']+' = '+value(b,'VALUE')+';\n'
            elif t=='variables_set': result+=f['VAR']+' = '+value(b,'VALUE')+';\n'
            elif t=='procedures_callnoreturn': result+=b.find('b:mutation',ns).get('name')+'();\n'
            elif t=='controls_if':
                i=0
                while b.find(f"b:value[@name='IF{i}']",ns) is not None:
                    result+=('else ' if i else '')+'if ('+value(b,'IF'+str(i))+') {\n'+statement(b,'DO'+str(i))+'}\n'; i+=1
                if b.find("b:statement[@name='ELSE']",ns) is not None: result+='else {\n'+statement(b,'ELSE')+'}\n'
            elif t=='inout_digital_write':
                pinmodes[f['PIN']]='OUTPUT'; result+='digitalWrite('+f['PIN']+','+f['STAT']+');\n'
            elif t=='inout_analog_write':
                pinmodes[f['PIN']]='OUTPUT'; result+='analogWrite('+f['PIN']+','+value(b,'Value')+');\n'
            elif t=='serial_setup': serials[f['SERIAL_ID']]=f['SERIAL_SPEED']
            elif t in ('serial_print','serial_printL'):
                result+='Serial.'+('println' if t=='serial_print' else 'print')+'('+value(b,'CONTENT')+');\n'
            else: raise ValueError('Unsupported statement block '+str(t))
            b=b.find('b:next/b:block',ns)
        return result
    main=root.find("b:block[@type='arduino_setup']",ns)
    if main is None: raise ValueError('One arduino_setup block is required')
    setup=statement(main,'MySetup'); loop=statement(main,'MyLoop')
    for b in root.findall("b:block[@type='procedures_defnoreturn']",ns): functions[fields(b)['NAME']]=statement(b,'STACK')
    header='// Generated from CAGEBOT XML; physical acceptance remains pending.\n#include <Arduino.h>\n'
    header+='\n'.join(t+' '+n+';' for n,t in declarations.items())+'\n'
    header+='\n'.join('void '+n+'();' for n in functions)+'\n'
    header+='\n'.join('void '+n+'() {\n'+body+'}\n' for n,body in functions.items())
    header+='void setup() {\n'+''.join('pinMode('+p+','+m+');\n' for p,m in pinmodes.items())
    header+=''.join(s+'.begin('+v+');\n' for s,v in serials.items())+setup+'}\n'
    return header+'void loop() {\n'+loop+'}\n'
