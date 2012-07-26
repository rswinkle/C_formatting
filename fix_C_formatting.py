import re, sys, string

if_re = re.compile(r"if\s*(\([^{]*\)) (\s*)(.*?\s*){", re.VERBOSE | re.DOTALL)		#correctly handles multiline comparisons and comments
for_re = re.compile(r"for (\(.*\)) (\s*)(.*?\s*){", re.VERBOSE)
do_re = re.compile(r"do \s*{", re.VERBOSE)
switch_re = re.compile(r"switch (\(.*\))\s*\n*\s*{", re.VERBOSE)
else_re	= re.compile(r"}\s* else \s*{", re.VERBOSE)				#need to correctly handle/ignore else if case
while_re = re.compile(r"while (\(.*\)) \s*\n\s*{", re.VERBOSE) #need to correctly handle the do while case ie } while() instead of }\n while()







#works
def fix_if(match):
	str_list = ['if ']
	str_list.append(match.group(1))
	str_list.append(' {')
	
	if any(c not in string.whitespace for c in match.group(3)):
		str_list.append(match.group(2))
		
	str_list.append(match.group(3))
	print(str_list)
	return ''.join(str_list)

#works
def fix_for(match):
	str_list = ['for ']
	str_list.append(match.group(1))
	str_list.append(' {')
	
	if any(c not in string.whitespace for c in match.group(3)):
		str_list.append(match.group(2))
		
	str_list.append(match.group(3))
	print(str_list)
	return ''.join(str_list)

#works
def fix_do(match):
	return 'do {'

#doesn't work 
def fix_switch(match):
	str_list = ['switch ']
	str_list.append(match.group(1))
	str_list.append(' {')
	return ''.join(str_list)

#works
def fix_else(match):
	return '} else {'

#need to keep testing
def fix_while(match):
	str_list = ['while ']
	str_list.append(match.group(1))
	str_list.append(' {')
	return ''.join(str_list)


def main():
	if len(sys.argv) < 2:
		print("Usage: python3 fix_C_formatting.py inputfile [outputfile]\n")
		return

	for i in sys.argv:
		print(i)

	try:
		c_file_string = open(sys.argv[1], "r").read()
		if len(sys.argv) == 3:
			output_file = open(sys.argv[2], "w")
	except:
		return			

#	if False:
	c_file_string = if_re.sub(fix_if, c_file_string)
	c_file_string = for_re.sub(fix_for, c_file_string)
	c_file_string = do_re.sub(fix_do, c_file_string)
	c_file_string = switch_re.sub(fix_switch, c_file_string)
	c_file_string = else_re.sub(fix_else, c_file_string)
	c_file_string = while_re.sub(fix_while, c_file_string)

	if len(sys.argv) == 3:
		output_file.write(c_file_string)
	else:
		print(c_file_string)

if __name__ == "__main__":
	main()





