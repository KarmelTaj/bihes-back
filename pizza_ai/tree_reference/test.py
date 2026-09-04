from trees import TopSemanticTree, ExpressSemanticTree

# TOP format
top = TopSemanticTree(
    flat_string="(ORDER can i have (PIZZAORDER (SIZE large ) (TOPPING pepperoni ) ) please )"
)

print(top.pretty_string())

# EXR format
exr = ExpressSemanticTree(
    flat_string="(ORDER (PIZZAORDER (SIZE LARGE) (TOPPING PEPPERONI)))"
)

print(exr.pretty_string())


######################

from semantic_matchers import is_unordered_exact_match

s1 = "(ORDER (SIZE LARGE) (TOPPING HAM))"
s2 = "(ORDER (TOPPING HAM) (SIZE LARGE))"

print(is_unordered_exact_match(s1, s2, "EXR"))



from semantic_matchers import is_semantics_only_unordered_exact_match

s1 = "(ORDER can i have (PIZZAORDER (SIZE large ) ) please )"
s2 = "(ORDER please (PIZZAORDER (SIZE large ) ) now )"

print(is_semantics_only_unordered_exact_match(s1, s2))




################




from trees import ExpressSemanticTree
from entity_resolution import PizzaSkillEntityResolver

resolver = PizzaSkillEntityResolver()

tree = ExpressSemanticTree(
    flat_string="(PIZZAORDER (SIZE large))"
)

resolved = resolver.resolve_tree_into_TGT(tree)

print(resolved.pretty_string())