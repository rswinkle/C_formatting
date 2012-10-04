import re, sys, string


#need to fix them all to handle single line no bracket versions
if_re = re.compile(r"if \s* (\([^{]*\)) (\s*.*?)\s*({|;)", re.VERBOSE | re.DOTALL)		#correctly handles multiline comparisons and comments
for_re = re.compile(r"for \W(.*?{)", re.VERBOSE | re.DOTALL) #no longer preserves comments
do_re = re.compile(r"do (\W+\s*.*?)\s*{", re.VERBOSE)     #maybe need to add that \W+ to all of these
switch_re = re.compile(r"switch \s* (\([^{]*\)) (\s*.*?)\s*{", re.VERBOSE)
else_re	= re.compile(r"}\s* else (\s*.*?)\s*{", re.VERBOSE)				#need to correctly handle/ignore else if case
while_re = re.compile(r"while \s* (\(.*\)) (\s*)(.*?\s*)({|;)", re.VERBOSE) #need to correctly handle the do while case ie } while() instead of }\n while()







#works
def fix_if(match):
	str_list = ['if ']
	str_list.append(match.group(1))
	str_list.append(' {')
	
	if not match.group(2).isspace():
		str_list.append(match.group(2))
	
	#print(match.group())
	#print(str_list)
	#print(''.join(str_list))
	return ''.join(str_list)


#seems to work but does not preserve comments anymore
#will fix later.  Probably currently hugely unoptimal cause I don't know
#the best pythonic way
def fix_for(match):
	str_list = ['for ']
	
	#does not handle in string
	s = match.group(0)
	cpp_comment = s.find('//')
	c_comment = s.find('/*')
	
	s2 = strip_comments(s)
	
	i = s2.find(';', s2.find(';')+1)  #get second ; in for loop
	paren = 1;
	while paren:
		if s2[i] == '(':
			paren += 1;
		if s2[i] == ')':
			paren -= 1;
		i += 1;
		
	s3 = s2[i:].lstrip()      #string = everything after closing for () with no leading whitespace
	
	if s3[0] != '{':              #if it doesn't have braces, don't mess with it because it's too much of a pain
		return match.group(0)     #to try to add the closing brace too
	
	str_list.append(s2[s2.find('('):i]+' {\n')
	j = len(s3[1:]) - len(s3[1:].lstrip())
	str_list.append(s3[1:1+j])
	
	print(match.group(0))
#	print(str_list)
	return ''.join(str_list)

	
	
#works
def fix_do(match):
	str_list = ['do {']

	if not match.group(1).isspace():
		str_list.append(match.group(1))
	

	#print(str_list)
	return ''.join(str_list)

#doesn't work 
def fix_switch(match):
	str_list = ['switch ']
	str_list.append(match.group(1))
	str_list.append(' {')
	
	if not match.group(2).isspace():
		str_list.append(match.group(2))
	
#	print(str_list)
	return ''.join(str_list)

#works
def fix_else(match):
	#have to do some text processing to handle else if case especially
	#if I want to handle something like else /* blag */ if
	#or else //blah\nif
	str1 = match.group(1)
	index = str1.find('if')
	if index < 0:
		a=1
	#	print('no if');
	else:
		else_if = str1[4:index]
	
	
	str_list = ['} else {']
	
	if not match.group(1).isspace():
		str_list.append(match.group(1))
	
	return ''.join(str_list)

#need to keep testing
def fix_while(match):
	str_list = ['while ']
	str_list.append(match.group(1))
	if match.group(4) is '{':
		str_list.append(' {')
	else:
		str_list.append(';')
		
	if any(c not in string.whitespace for c in match.group(3)):
		str_list.append(match.group(2))
		
#	print(str_list)
	return ''.join(str_list)



def strip_comments(s):
	cpp_comment = s.find('//')
	c_comment = s.find('/*')
	
	while True:
		cpp_comment = s.find('//')
		c_comment = s.find('/*')
		c_comment = c_comment if c_comment != -1 else len(s);
		cpp_comment = cpp_comment if cpp_comment != -1 else len(s);
		
		if c_comment == len(s) and c_comment == cpp_comment:
			break
		
		if c_comment < cpp_comment:
			s = s.replace(s[c_comment:s.find('*/')+2], '')
			
			if cpp_comment < len(s):
				s = s.replace(s[cpp_comment:s.find('\n', cpp_comment)])
		else:
			s = s.replace(s[cpp_comment:s.find('\n', cpp_comment)])
			
			if c_comment < len(s):
				s = s.replace(s[c_comment:s.find('*/')+2], '')
	
	return s
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
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





