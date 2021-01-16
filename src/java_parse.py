import javalang

source = '''
package javalang.foo.bar;

class Test extends BaseTest{

@TaskAttribute
public int x;

@TaskAttribute(required = true)
private int y;

@TaskAttribute(required = false)
public double xPos;

public String name;

}

'''

def _get_top_level_class(java_ast):
    "Return top level class."
    return next(java_ast.filter(javalang.tree.ClassDeclaration))[1]


def _get_annotations(field_dec) -> list:
    "Return the annotations of a field."
    annotations = []
    for _, node in field_dec.filter(javalang.tree.Annotation):
        if annotation.name == "TaskAttribute":
            annotations.append(node)
    return annotations

def _get_fields(class_tree) -> list:
    "Return field information for a given class."
    fields = []
    for _ , node in class_tree.filter(javalang.tree.FieldDeclaration):
        field = {}
        field["name"] = (node.declarators[0].name
                         if node.declarators else "?")
        field["type"] = node.type.name if node.type else "?"
        annotations = _get_annotations(node)
        eles = [a.element for a in annotations if a.element]
        eles = [e for sublist in eles for e in sublist]
        req = [e.name == "required" and e.value.value == "true"
               for e in eles if e.name and e.value and e.value.value]
        required = any(req)
        field["required"] = required
        fields.append(field)
    return fields


def get_java_class_info(class_path) -> dict:
    "Return field information about a java class."
    source = None
    with open(class_path, 'r') as fd:
        source = fd.read()
    java_ast = javalang.parse.parse(source)
    top_class = _get_top_level_class(java_ast)
    fields = _get_fields(top_class)
    return {"fields": fields}
    

ast = javalang.parse.parse(source)

top_class = _get_top_level_class(ast)
fields = get_fields(top_class)

# We want
# 1. name of field
# 2. type of field
# 3. contains annotation
# 4. required?
