import re

with open('core/views.py', 'r') as f:
    content = f.read()

# Fix the raw strings
content = re.sub(r'details \+= "\nBłędy:\n" \+ "\n"\.join\(errors\[:10\]\)', r'details += "\\nBłędy:\\n" + "\\n".join(errors[:10])', content)
content = re.sub(r'details \+= f"\n\.\.\.oraz \{len\(errors\) - 10\} innych\."', r'details += f"\\n...oraz {len(errors) - 10} innych."', content)

with open('core/views.py', 'w') as f:
    f.write(content)
