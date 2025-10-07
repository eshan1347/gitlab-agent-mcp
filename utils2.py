from copy import deepcopy
from typing import Any, Dict, Set, List
import json
from utils import fix_schema

def jsonConv(schema :Dict[str, Any]) -> Dict[str, Any]:
    schema = fix_schema(schema)
    print(f'fix ed: {json.dumps(schema, indent=2)}\n\n')
    val_prop_keys = ['type', 'description', 'enum', 'default', 'minimum', 'maximum', 'minLength', 'maxLength', 'pattern', 'items', 'format']
    val_schema_keys = ['type', 'properties', 'required']
    res = {}
    for key in schema:
        # print(f'Schema Key: {key}')
        if key in val_schema_keys:
            if key == 'properties':
                res2 = {} 
                for prop in schema[key]:
                    res3 = {}
                    for prop_key in schema[key][prop]:
                        # print(f'Prop key: {prop_key}')
                        if prop_key in val_prop_keys:
                            temp = schema[key][prop][prop_key]
                            if isinstance(temp, List):
                                # if all(isinstance(t, str) for t in temp):
                                #     temp = {'anyOf':[{prop_key: ty} for ty in temp]}
                                # else:                                    
                                if prop_key == 'type':
                                    for ty in temp:
                                        if ty != 'null':
                                            temp = ty
                                            break
                                    if not isinstance(temp, str):
                                        temp = 'null'
                                elif prop_key == 'enum':
                                    pass
                                else:
                                    temp = temp[0]
                            elif isinstance(temp, Dict) and prop_key != "items":
                                continue
                            res3[prop_key] = temp
                    if res3:
                        res2[prop] = res3
                if res2:
                    res[key] = res2
            else:
                res[key] = schema[key]
    return res

if __name__=='__main__':
    with open('./test.json', 'r') as f:
        jason = json.load(f)
    print(json.dumps(jsonConv(jason), indent=2))