import re, sys, string, glob
from os.path import *
from collections import namedtuple



if_regex     = r"(?=(if\W.*?{))"
for_regex    = r"(?=(for\W.*?{))"
do_regex     = r"(?=(do\W.*?{))"
switch_regex = r"(?=(switch\W.*?{))"
else_regex   = r"(?=(else\W.*?{))"
while_regex  = r"(?=(while\W.*?{))"



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
	paren = 0
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

#find and return position of first uncommented non-whitespace character in s starting at i
def find_first(s, i, end):
	while i < end:
		if s[i:i+2] == '/*':
			i = s.find('*/', i+2) + 1    # set i to first character after closing - 1 because increment at end */
		elif s[i:i+2] == '//':
			i = s.find('\n', i+2)        # set i to \n because inc at end
		elif not s[i].isspace():
			break
			
		i += 1
		
	return i;


def in_comment(i, comment_list):
	if not comment_list:
		return False
		
	j = 0
	while i < comment_list[j].start:
		j += 1
		if j >= len(comment_list):
			return False
			
	if i < comment_list[j].end:
		return True
		
	return False




    
    
#works
def fix_if(match, file_string, comment_list):
	m_start = match.start(1)
	m_end = match.end(1)
	start_len = 2


	if in_comment(m_start, comment_list):
		return file_string, m_start + start_len  #return position right after if
	if in_comment(m_end-1, comment_list): #return position after {  This won't
		return file_string, m_end         #fix something like for() /* { */\n/t { oh well
                                       
	
	#print('$',match.span(1),' "'+match.group(1)+'"')
	#does not handle in string
	s = match.group(1)

	after_paren = find_open_close_paren(s, start_len, len(s))
	#after_paren is first char after )
	
	i = find_first(s, after_paren, len(s))
	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	#brace is the last character and first uncommented
	s = 'if ' + s[start_len:after_paren] + ' {' + s[after_paren:-1]   #cut off last character, the brace
	#print(s,'\n===\n')
	
	return file_string[:m_start] + s + file_string[m_end:], m_end








#python does short circuit boolean expressions
#seems to work but does not preserve comments anymore
#will fix later.  Probably currently hugely unoptimal cause I don't know
#the best pythonic way
def fix_for(match, file_string, comment_list):
	m_start = match.start(1)
	m_end = match.end(1)
	start_len = 3
	
	if in_comment(m_start, comment_list):
		return file_string, m_start + start_len  #return position right after for
	if in_comment(m_end-1, comment_list): #return position after {  This won't
		return file_string, m_end         #fix something like for() /* { */\n/t { oh well
                                       
	
	print('$',match.span(1),' "'+match.group(1)+'"')
	#does not handle in string
	s = match.group(1)

	print(start_len, m_end)
	after_paren = find_open_close_paren(s, start_len, len(s))

	#returning len(s)+1 can still happen if the match starts in a string literal
	#or something other than a comment
	if after_paren >= len(s):
		return file_string, m_start + start_len
	#after_paren is first char after )
	
	i = find_first(s, after_paren, len(s))
	if i >= len(s):
		return file_string, m_start + start_len


	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		print('first uncommented char is "'+ s[i] + '" at ', i)
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	#brace is the last character and first uncommented
	s = 'for ' + s[start_len:after_paren] + ' {' + s[after_paren:-1]   #cut off last character, the brace
	#print(s,'\n===\n')
	
	return file_string[:m_start] + s + file_string[m_end:], m_end




#works
def fix_do(match, file_string, comment_list):
	m_start = match.start(1)
	m_end = match.end(1)
	start_len = 2


	if in_comment(m_start, comment_list):
		return file_string, m_start + start_len  #return position right after do
	if in_comment(m_end-1, comment_list): #return position after {  This won't
		return file_string, m_end         #fix something like for() /* { */\n/t { oh well
                                       
	
	#print('$',match.span(1),' "'+match.group(1)+'"')
	#does not handle in string
	s = match.group(1)

	i = find_first(s, start_len, len(s))
	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	#brace is the last character and first uncommented
	s = 'do {' + s[start_len:-1]   #cut off last character, the brace
	#print(s,'\n===\n')
	
	return file_string[:m_start] + s + file_string[m_end:], m_end




#doesn't work 
def fix_switch(match, file_string, comment_list):
	m_start = match.start(1)
	m_end = match.end(1)
	start_len = 6

	if in_comment(m_start, comment_list):
		return file_string, m_start + start_len  #return position right after if
	if in_comment(m_end-1, comment_list): #return position after {  This won't
		return file_string, m_end         #fix something like for() /* { */\n/t { oh well
                                       
	
	#print('$',match.span(1),' "'+match.group(1)+'"')
	#does not handle in string
	s = match.group(1)

	after_paren = find_open_close_paren(s, start_len, len(s))
	#after_paren is first char after )
	
	i = find_first(s, after_paren, len(s))
	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	#brace is the last character and first uncommented
	s = 'switch ' + s[start_len:after_paren] + ' {' + s[after_paren:-1]   #cut off last character, the brace
	#print(s,'\n===\n')
	
	return file_string[:m_start] + s + file_string[m_end:], m_end






#works
def fix_else(match, file_string, comment_list):
	m_start = match.start(1)
	m_end = match.end(1)
	start_len = 4


	if in_comment(m_start, comment_list):
		return file_string, m_start + start_len  #return position right after if
	if in_comment(m_end-1, comment_list): #return position after {  This won't
		return file_string, m_end         #fix something like for() /* { */\n/t { oh well
                                       
	
	#print('$',match.span(1),' "'+match.group(1)+'"')
	#does not handle in string
	s = match.group(1)
	
	i = find_first(s, start_len, len(s))

	#if s[i:i+2] == 'if':
		#return file_string, m_start+start_len   #ignore else if case for now, most people put them on the same line anyway

	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	#brace is the last character and first uncommented
	s = 'else {' + s[start_len:-1]   #cut off last character, the brace
	#print(s,'\n===\n')
	
	return file_string[:m_start] + s + file_string[m_end:], m_end




#need to keep testing
def fix_while(match, file_string, comment_list):
	m_start = match.start(1)
	m_end = match.end(1)
	start_len = 5

	if in_comment(m_start, comment_list):
		return file_string, m_start + start_len  #return position right after if
	if in_comment(m_end-1, comment_list): #return position after {  This won't
		return file_string, m_end         #fix something like for() /* { */\n/t { oh well
                                       
	
	#print('$',match.span(1),' "'+match.group(1)+'"')
	#does not handle in string
	s = match.group(1)

	after_paren = find_open_close_paren(s, start_len, len(s))
	#after_paren is first char after )
	
	i = find_first(s, after_paren, len(s))
	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	#brace is the last character and first uncommented
	s = 'while ' + s[start_len:after_paren] + ' {' + s[after_paren:-1]   #cut off last character, the brace
	#print(s,'\n===\n')
	
	return file_string[:m_start] + s + file_string[m_end:], m_end


	
comment = namedtuple('comment', ['start', 'end'])

#returns a list of tuples of comment start and end, ie s[start:end] is the comment
def find_comments(s, start=0):
	comment_list = [] #list of tuples (index, comment text)
	
	i = start
	while True:
		cpp_comment = s.find('//', i)
		c_comment = s.find('/*', i)
		c_comment = c_comment if c_comment != -1 else len(s);
		cpp_comment = cpp_comment if cpp_comment != -1 else len(s);
		
		if c_comment == len(s) and c_comment == cpp_comment:
			break
		
		
		end = 0
		if c_comment < cpp_comment:
			end = s.find('*/', c_comment) + 2
			comment_list.append(comment(c_comment, end))
			i = end
		else:
			end = s.find('\n', cpp_comment)
			comment_list.append(comment(cpp_comment, end))
			i = end
	
	return comment_list
	
	
	

	
	
	
def fix_construct(regex, fix_func, c_file_string, comment_list):
	match = regex.search(c_file_string)
	while match:
		c_file_string, pos = fix_func(match, c_file_string, comment_list)
		comment_list = find_comments(c_file_string, pos) 
		match = regex.search(c_file_string, pos)
	
	return c_file_string



regexes       = [if_re, for_re, do_re, switch_re, else_re, while_re]
fix_functions = [fix_if, fix_for, fix_do, fix_switch, fix_else, fix_while]



def main():
	if len(sys.argv) < 2:
		print("Usage: python3 fix_C_formatting.py directory | inputfile [outputfile]\n")
		print("If the first argument is a directory, this script will edit every c and cpp file it finds and overwrite them")
		return

	for i in sys.argv:
		print(i)

	file_list = []
	directory = ''

	if isdir(sys.argv[1]):
		directory = sys.argv[1] if sys.argv[1][-1] == '/' else sys.argv[1] + '/'
		file_list   =   glob.glob(sys.argv[1] + '*.c')
		file_list += glob.glob(sys.argv[1] + '*.cpp')
	else:
		c_files.append(sys.argv[1])

	for f in file_list:
		try:
			c_file_string = open(f, "r").read()
		except:
			return
		
		comment_list = find_comments(c_file_string)
		
		for regex, fix_func in zip(regexes, fix_functions):
			c_file_string = fix_construct(regex, fix_func, c_file_string, comment_list)

		if directory:
			open(f, 'w').write(c_file_string)
		elif len(sys.argv) == 3:
			open(sys.argv[2], 'w').write(c_file_string)
		else:
			print(c_file_string)


	#regex = for_re
	#fix_func = fix_for

	#match = regex.search(c_file_string)
	#while match:
		#c_file_string, pos = fix_func(match, c_file_string, comment_list)
		#comment_list = find_comments(c_file_string, pos) 
		#match = regex.search(c_file_string, pos)


if __name__ == "__main__":
	main()





