import re, sys, string

if_regex     = r"if \s* (\([^{]*\)) (\s*.*?)\s*({|;)"
for_regex    = r"(?=(for\W.*?{))"
do_regex     = r"do (\W+\s*.*?)\s*{"
switch_regex = r"switch \s* (\([^{]*\)) (\s*.*?)\s*{"
else_regex   = r"}\s* else (\s*.*?)\s*{"
while_regex  = r"while \s* (\(.*\)) (\s*)(.*?\s*)({|;)"



#need to fix them all to handle single line no bracket versions
if_re     = re.compile(if_regex, re.VERBOSE | re.DOTALL)   #correctly handles multiline comparisons and comments
for_re    = re.compile(for_regex, re.VERBOSE | re.DOTALL)  #no longer preserves comments
do_re     = re.compile(do_regex, re.VERBOSE)               #maybe need to add that \W+ to all of these
switch_re = re.compile(switch_regex, re.VERBOSE)
else_re   = re.compile(else_regex, re.VERBOSE)             #need to correctly handle/ignore else if case
while_re  = re.compile(while_regex, re.VERBOSE)            #need to correctly handle the do while case ie } while() instead of }\n while()



def insert(str1, str2, pos):
	return str1[:pos] + str2 + str1[pos:]

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

def enum(**enums):
    return type('Enum', (), enums)

FSM = enum(PREOPEN=0, OPEN=1, CCOMMENT=2, CPPCOMMENT=4)
    

    
#returns the position of the first character after the ) of the next ( 
#starting at i, skipping comments of course
def find_open_close_paren(s, i, end):
	while i < end:
		if s[i] == '(':
			paren += 1
		elif s[i] == ')':
			paren -= 1;
			if not paren:
				break
		elif s[i:i+2] == '/*':
			i = s.find('*/', i+2) + 1    # set i to first character after closing - 1 because increment at end */
		elif s[i:i+2] == '//':
			i = s.find('\n', i+2)        # set i to \n because inc at end
		
		i += 1
		
	return i + 1;
	

#find and return position of first uncommented character c in s starting at i
def find_first_of(s, i, c):
	while True:
		if s[i] == c:
			break
		elif s[i:i+2] == '/*':
			i = s.find('*/', i+2) + 1    # set i to first character after closing - 1 because increment at end */
		elif s[i:i+2] == '//':
			i = s.find('\n', i+2)        # set i to \n because inc at end
		
		i += 1
		
	return i;

#find and return position of first uncommented character in s starting at i
def find_first(s, i, end):
	while i < end:
		if s[i:i+2] == '/*':
			i = s.find('*/', i+2) + 1    # set i to first character after closing - 1 because increment at end */
		elif s[i:i+2] == '//':
			i = s.find('\n', i+2)        # set i to \n because inc at end
		else:
			break
			
		i += 1
		
	return i;
    
    
    
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


#python does short circuit boolean expressions
#seems to work but does not preserve comments anymore
#will fix later.  Probably currently hugely unoptimal cause I don't know
#the best pythonic way
def fix_for(match, file_string):
	str_list = ['for ']
	
	print(match.group(1))
	#does not handle in string
	s = match.group(1)

	

	i = find_open_close_paren(s, 3)
	
	if (i == match.end(1)):
		return file_string;
	brace = find_first(s, i)
	if i == match.end(1):
		return file_string
	
	if brace != '{'          #could also check if brace is not last character
		return file_string

	#else brace is the last character according to 
	s = 'for ' + s[3:i] + ' {' + s[i:-1]   #cut off last character, the brace
	
	return file_string[:match.start(1)] + s + file_string[match.end(1):]
	
	##############################
	
	



"""
	s2, comments = strip_comments(s)
	
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
		print('no brace')
		return match.group(1)     #to try to add the closing brace too
	
	
	str_list.append(s2[s2.find('('):i]+' {\n')
	j = len(s3[1:]) - len(s3[1:].lstrip())
	str_list.append(s3[1:1+j])
	

	print(str_list,'\n')
	return ''.join(str_list)
"""
	
	
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
	comments = [] #list of tuples (index, comment text)
	
	while True:
		cpp_comment = s.find('//')
		c_comment = s.find('/*')
		c_comment = c_comment if c_comment != -1 else len(s);
		cpp_comment = cpp_comment if cpp_comment != -1 else len(s);
		
		if c_comment == len(s) and c_comment == cpp_comment:
			break
		
		#only remove one per iteration in case we have comment tokens inside
		#each other ie // baseunadteou/*
		# or /* bseuaoeusdao // */
		end = 0
		if c_comment < cpp_comment:
			end = s.find('*/') + 2
			comments.append((c_comment, s[c_comment:end]))
			s = s.replace(s[c_comment:end], '')
		else:
			end = s.find('\n', cpp_comment)
			comments.append((cpp_comment, s[cpp_comment:end]))
			s = s.replace(s[cpp_comment:end], '')
	
	return s, comments
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
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
		
		
		
	c_file_string_2 = c_file_string;
	for match in for_re.finditer(c_file_string):
		c_file_string_2 = fix_for(match, c_file_string_2)

	c_file_string = for_re.sub(fix_for, c_file_string)
	if False:
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





