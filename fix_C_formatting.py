import re, sys, string, glob, argparse, os
from os.path import *
from collections import namedtuple



if_regex     = r"\s(?=(if\W.*?{))"
for_regex    = r"\s(?=(for\W.*?{))"
do_regex     = r"\s(?=(do\W.*?{))"
switch_regex = r"\s(?=(switch\W.*?{))"
else_regex   = r"\s(?=(else\W.*?{))"
while_regex  = r"\s(?=(while\W.*?{))"



#need to fix them all to handle single line no bracket versions
if_re     = re.compile(if_regex, re.VERBOSE | re.DOTALL)   #correctly handles multiline comparisons and comments
for_re    = re.compile(for_regex, re.VERBOSE | re.DOTALL)  #no longer preserves comments
do_re     = re.compile(do_regex, re.VERBOSE)               #maybe need to add that \W+ to all of these
switch_re = re.compile(switch_regex, re.VERBOSE)
else_re   = re.compile(else_regex, re.VERBOSE)             #need to correctly handle/ignore else if case
while_re  = re.compile(while_regex, re.VERBOSE)            #need to correctly handle the do while case ie } while() instead of }\n while()


be_cautious = False


def insert(str1, str2, pos):
	return str1[:pos] + str2 + str1[pos:]

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

def enum(**enums):
    return type('Enum', (), enums)

    

    
#returns the positions of the first ( and matching ) 
#starting at i, skipping comments of course
def find_open_close_paren(s, i, end):
	paren = 0
	open_paren = -1
	while i < end:
		if s[i] == '(':
			if open_paren < 0:
				open_paren = i
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

	return open_paren, i;

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
	while j < len(comment_list):
		if i > comment_list[j].start:
			if i < comment_list[j].end:
				return True
		else:
			return False

		j += 1

	
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

	#does not handle in string
	s = match.group(1)
	#print(match.span(1), '"'+s+'"')

	open_paren, close_paren = find_open_close_paren(s, start_len, len(s))
	after_paren = close_paren + 1

	i = find_first(s, after_paren, len(s))
	if i >= len(s):  #must not be valid (maybe we matched inside a string literal)
		return file_string, m_start + start_len  # can just check here instead of after paren too
	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	nl_after_paren = s.find('\n', after_paren)
	# find amount to add to after_paren to get rid of any trailing whitespace
	# if there is any non-whitespace character after ) before {, keep everything

	if not s[after_paren:nl_after_paren].isspace():
		nl_after_paren = 0
	else:
		nl_after_paren = len(s[after_paren:nl_after_paren]) - len(s[after_paren:nl_after_paren].lstrip(string.whitespace.replace('\n','')))

	if not be_cautious:
		s = 'if '+ s[start_len:open_paren].strip() +'(' +  s[open_paren+1:close_paren].strip() + ') {' + s[after_paren+nl_after_paren:-1]   #cut off last character, the brace
	else:
		s = 'if '+ s[start_len:open_paren].strip() + s[open_paren:close_paren+1] + ' {' + s[after_paren+nl_after_paren:-1]   #cut off last character, the brace
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
                                   

	#does not handle in string
	s = match.group(1)

	#print(start_len, m_end)
	open_paren, close_paren = find_open_close_paren(s, start_len, len(s))
	after_paren = close_paren + 1

	#returning len(s) can still happen if the match starts in a string literal
	#or something other than a comment but we can just check once after find_first
	#after_paren is first char after )
	
	i = find_first(s, after_paren, len(s))
	if i >= len(s):
		return file_string, m_start + start_len


	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		print('first uncommented char is "'+ s[i] + '" at ', i)
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	nl_after_paren = s.find('\n', after_paren)
	# find amount to add to after_paren to get rid of any trailing whitespace
	# if there is any non-whitespace character after ) before {, keep everything

	if not s[after_paren:nl_after_paren].isspace():
		nl_after_paren = 0
	else:
		nl_after_paren = len(s[after_paren:nl_after_paren]) - len(s[after_paren:nl_after_paren].lstrip(string.whitespace.replace('\n','')))

	#brace is the last character and first uncommented
	if not be_cautious:
		s = 'for '+ s[start_len:open_paren].strip() + '(' +  s[open_paren+1:close_paren].strip() + ') {' + s[after_paren+nl_after_paren:-1]   #cut off last character, the brace
	else:
		s = 'for '+ s[start_len:open_paren].strip() + s[open_paren:close_paren+1] + ' {' + s[after_paren+nl_after_paren:-1]   #cut off last character, the brace

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
	if i >= len(s):
		return file_string, m_start + start_len
	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	#brace is the last character and first uncommented
	s = 'do {' + s[start_len:-1].lstrip()   #cut off last character, the brace
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

	open_paren, close_paren = find_open_close_paren(s, start_len, len(s))
	after_paren = close_paren + 1
	
	i = find_first(s, after_paren, len(s))
	if i >= len(s):
		return file_string, m_start + start_len
	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	nl_after_paren = s.find('\n', after_paren)
	# find amount to add to after_paren to get rid of any trailing whitespace
	# if there is any non-whitespace character after ) before {, keep everything

	if not s[after_paren:nl_after_paren].isspace():
		nl_after_paren = 0
	else:
		nl_after_paren = len(s[after_paren:nl_after_paren]) - len(s[after_paren:nl_after_paren].lstrip(string.whitespace.replace('\n','')))


	#brace is the last character and first uncommented
	if not be_cautious:
		s = 'switch ' +  s[start_len:open_paren].strip() + '(' +  s[open_paren+1:close_paren].strip() + ') {' + s[after_paren+nl_after_paren:-1]   #cut off last character, the brace
	else:
		s = 'switch '+ s[start_len:open_paren].strip() + s[open_paren:close_paren+1] + ' {' + s[after_paren+nl_after_paren:-1]   #cut off last character, the brace

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
	if i >= len(s):
		return file_string, m_start + start_len

	#if s[i:i+2] == 'if':
		#return file_string, m_start+start_len   #ignore else if case for now, most people put them on the same line anyway

	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	#brace is the last character and first uncommented
	s = 'else {' + s[start_len:-1].lstrip()   #cut off last character, the brace
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

	open_paren, close_paren = find_open_close_paren(s, start_len, len(s))
	after_paren = close_paren + 1
	
	i = find_first(s, after_paren, len(s))
	if i >= len(s):
		return file_string, m_start + start_len
	#i is pos of first uncommented char after 
	
	if s[i] != '{':         #if it's not a brace, it's a statement or new block s
		return file_string, m_start + start_len  #don't touch if it doesn't have braces (brace at end of match is for something else)

	nl_after_paren = s.find('\n', after_paren)
	if not s[after_paren:nl_after_paren].isspace():
		nl_after_paren = 0
	else:
		nl_after_paren = len(s[after_paren:nl_after_paren]) - len(s[after_paren:nl_after_paren].lstrip(string.whitespace.replace('\n','')))


	#brace is the last character and first uncommented
	if not be_cautious:
		s = 'while ' + s[start_len:open_paren].strip() + '(' +  s[open_paren+1:close_paren].strip() + ') {' + s[after_paren+nl_after_paren:-1]   #cut off last character, the brace
	else:
		s = 'while '+ s[start_len:open_paren].strip() + s[open_paren:close_paren+1] + ' {' + s[after_paren+nl_after_paren:-1]   #cut off last character, the brace

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
			end = s.find('\n', cpp_comment) + 1
			comment_list.append(comment(cpp_comment, end))
			i = end
	
	return comment_list
	
	
	

def recurse_dir(root, filetypes):                                           # for a root dir
	files = []
	for (thisdir, subshere, fileshere) in os.walk(root):    # generate dirs in tree
		for t in filetypes:
			files.extend(glob.glob(thisdir+'/*'+t))
		#print('[' + thisdir + ']')
		#for fname in fileshere:                             # files in this dir
			#if any(fname.endswith(t) for t in filetypes):
				#files.append(os.path.join(thisdir, fname))             # add dir name prefix
				#print(path)
	return files


	
	
	
def fix_construct(regex, fix_func, c_file_string):
	match = regex.search(c_file_string)
	comment_list = []
	pos = 0
	while match:
		comment_list = find_comments(c_file_string, pos)
		c_file_string, pos = fix_func(match, c_file_string, comment_list) 
		match = regex.search(c_file_string, pos)
	
	return c_file_string



regexes       = [if_re, for_re, do_re, switch_re, else_re, while_re]
fix_functions = [fix_if, fix_for, fix_do, fix_switch, fix_else, fix_while]


suffix_help ="""specify a suffix string to append to input files for output,
ie -s _fixed writes the results of fixing file1.cpp to file1.cpp_fixed"""

cautious_help ="""don't do some things (like stripping whitespace inside parens ie without -c, if ( a == b ) { becomes if (a == b) {"""

def main():
	parser = argparse.ArgumentParser(description="Convert C/C++ files to The One True Brace Style")
	parser.add_argument("-i", "--input", nargs="+", default=[sys.stdin], help="the input file(s) and directories (default = stdin)")
	parser.add_argument("-f", "--filetypes", nargs="+", default=[".c", ".cpp"], help="the filetypes to fix in directories (default = ['.c', '.cpp]")
	parser.add_argument("-r", "--recursive", action="store_true", help="search through given directories recursively")
	parser.add_argument("-c", "--cautious", action="store_true", help=cautious_help)
	group = parser.add_mutually_exclusive_group()
	group.add_argument("-o", "--overwrite", action="store_true", help="overwrite fixed files (Make a backup or use source control!!)")
	group.add_argument("-s", "--suffix", help=suffix_help)

	args = parser.parse_args()
	print(args)


	be_cautious = args.cautious



	file_list = []
	if args.input[0] == sys.stdin:
		file_list.append(sys.stdin)
	else:
		for i in args.input:
			if isdir(i):
				if args.recursive:
					file_list += recurse_dir(i, args.filetypes)
				else:
					for t in args.filetypes:
						file_list += glob.glob(i+'/*'+t)
			else:
				file_list.append(i)


	for f in file_list:
		if f == sys.stdin:
			c_file_string = f.read()
		else:
			try:
				c_file_string = open(f, "r").read()
			except:
				return
		
		#comment_list = find_comments(c_file_string)
		
		for regex, fix_func in zip(regexes, fix_functions):
			c_file_string = fix_construct(regex, fix_func, c_file_string)


		if args.overwrite:
			open(f, 'w').write(c_file_string)
		elif args.suffix:
			open(f+args.suffix, 'w').write(c_file_string)
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





