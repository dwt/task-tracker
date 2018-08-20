#!/usr/bin/env python3


import re

class Todo:
    
    # TODO retain offsets of all matches, so they can easily be used for a highlighter
    
    class REGEX:
        # TODO require whitespace at beginning
        DONE = re.compile(r'^\s*(x)\s')
        CONTEXTS = re.compile(r'@(\w+)')
        PROJECTS = re.compile(r'\+(\w+)')
        TAGS = re.compile(r'''
            (\w+):
            (?:(?P<simple>\w+)
            |\'(?P<single>[\w\s]+)\'
            |\"(?P<double>[\w\s]+)\")
        ''', flags=re.X
        )
    
    def __init__(self, line):
        self.line = line
        self.children = []
    
    @classmethod
    def from_lines(cls, lines):
        "Tasks become children of Tasks when they are indented by two spaces after another task."
        todos = []
        for line in lines.strip().split('\n'):
            todo = Todo(line)
            if todo.has_prefix():
                todos[-1].add_child(todo)
            else:
                todos.append(todo)
        return todos
    
    def __str__(self):
        return '\n'.join([self.line] + list(map(str, self.children)))
    
    def __repr__(self):
        return f'<Todo(line={self.line!r}, children={self.children!r})>'
    
    @property
    def is_done(self):
        return not not self.REGEX.DONE.match(self.line)
    
    @property
    def contexts(self):
        return self.REGEX.CONTEXTS.findall(self.line)
    
    @property
    def projects(self):
        return self.REGEX.PROJECTS.findall(self.line)
    
    @property
    def tags(self):
        matches = self.REGEX.TAGS.findall(self.line)
        return dict((
            match[0],
            match[1] or match[2] or match[3]
        ) for match in matches)
    
    @property
    def prefix(self):
        return re.match(r'^(\s*)', self.line).groups()[0] or ''
    
    def has_prefix(self):
        return len(self.prefix) > 0
    
    def has_children(self):
        return len(self.children) > 0
    
    def add_child(self, child):
        if self.has_children() and child.is_more_indented_than(self.children[-1]):
            self.children[-1].add_child(child)
        else:
            self.children.append(child)
    
    def is_more_indented_than(self, other):
        return len(self.prefix) > len(other.prefix)
    
    def children_tagged(self, *tags):
        for child in self.children:
            if child.has_tags(*tags):
                yield child
    
    def children_not_tagged(self, *tags):
        "Does not have any of the tags given"
        for child in self.children:
            if child.has_no_tags(*tags):
                yield child
    
    def has_tags(self, *tags):
        "Accepts 'tag:' if the value doesn't matter or 'tag:foo' for specific values"
        for tag in tags:
            if tag.endswith(':'): # value doesn't matter:
                if tag not in self.tags.keys():
                    return False
            else:
                key, value = tag.split(':')
                if self.tags.get(key, None) != value:
                    return False
        return True
    
    def has_no_tags(self, *tags):
        "Accepts 'tag:' if the value doesn't matter or 'tag:foo' for specific values"
        for tag in tags:
            if self.has_tags(tag):
                return False
        
        return True

from pyexpect import expect
from unittest import TestCase

class TodoTest(TestCase):
    
    def test_simple(self):
        expect(str(Todo(''))) == ''
        
        simple = 'I am a simple todo item'
        todo = Todo(simple)
        expect(str(todo)) == simple
    
    def test_done_item(self):
        expect(Todo('fnord').is_done).is_false()
        expect(Todo('x fnord').is_done).is_true()
    
    def test_contexts(self):
        expect(Todo('foo').contexts) == []
        expect(Todo('foo @context1 baz @context2').contexts) == ['context1', 'context2']
    
    def test_projects(self):
        expect(Todo('foo').projects) == []
        expect(Todo('foo +project1 bar +project2').projects) == ['project1', 'project2']
    
    def test_tags(self):
        expect(Todo('foo').tags) == dict()
        expect(Todo('foo id:234 tag2:val2').tags) == dict(
            id='234',
            tag2='val2',
        )
    
    def test_tags_with_spaces(self):
        expect(Todo('foo foo:bar sprint:"fnordy fnord roughnecks"').tags) == { 'sprint': "fnordy fnord roughnecks", 'foo':'bar' }
        expect(Todo("foo foo:bar sprint:'fnordy fnord roughnecks'").tags) == { 'sprint': "fnordy fnord roughnecks", 'foo':'bar' }
    

from textwrap import dedent
class MultipleTodosTest(TestCase):
    
    def test_multi_lines(self):
        todos = Todo.from_lines(dedent("""
        first
        x second
        third id:2346 sprint:'fnordy fnord roughnecks'
        """))
        
        expect(todos).has_length(3)
        expect(str(todos[0])) == 'first'
        expect(todos[1].is_done).is_true()
        expect(todos[2].tags) == { 'id': '2346', 'sprint': 'fnordy fnord roughnecks' }
    
    def test_sub_tasks(self):
        lines = dedent("""
        first
          x second
          third id:2346 sprint:'fnordy fnord roughnecks'
        """)
        todos = Todo.from_lines(lines)
        
        expect(todos).has_length(1)
        parent = todos[0]
        expect(parent.line) == 'first'
        expect(str(parent)) == lines.strip()
        expect(parent.children[0].is_done).is_true()
        expect(parent.children[1].tags) == { 'id': '2346', 'sprint': 'fnordy fnord roughnecks' }
    
    def test_sub_sub_tasks(self):
        todos = Todo.from_lines(dedent("""
        first
          x second
            third id:2346 sprint:'fnordy fnord roughnecks'
          fourth +project1
        """))
        
        expect(todos).has_length(1)
        parent = todos[0]
        expect(parent.line).contains('first')
        expect(parent.children).has_length(2)
        expect(parent.children[0].children[0].tags) == { 'id': '2346', 'sprint': 'fnordy fnord roughnecks' }
        expect(parent.children[1].projects) == ['project1']
    
    def test_children_tagged(self):
        parent = Todo.from_lines(dedent("""
        parent
            child1 status:doing
            child2
            child3 status:doing
            child4 status:done
        """))[0]
        
        expect(parent.line).contains('parent')
        doing = list(parent.children_tagged('status:doing'))
        expect(doing).has_length(2)
        expect(doing[0].line).contains('child1')
        expect(doing[1].line).contains('child3')
        
        waiting = list(parent.children_not_tagged('status:doing', 'status:done'))
        expect(waiting).has_length(1)
        expect(waiting[0].line).contains('child2')
        
    def _test_expanded_stories(self):
        """
        The idea here is that we want tasks to be expanded, so we can write their description down.
        
        This should be
        a) notified by a marker. Potentially /^ \s* + \s* /x, but also maybe just by being tagged with expand:true or @expanded
        b) be indented two levels, so we can still recover subtasks (only one level indented)
        
        first
                This is a longer description of what this story is to implement.
                It can of course be multiple lines and can use **markdown** or similar 
                formatting rules. Probably what your native bug tracker supports.
            second < this is still a subtask of first
        
        Leaning towards the idea of having a workflow with @contexts
        * You write the description and it is parsed as a description.
        * If a description is parsed, the tag @expanded is auto added
        * If the tag is removed, the description is hidden on serialization
        
        This should allow to easily add a description without having to add a 
        cumbersome @context while still allowing the list to be  switched.
        
        Ideally it would something like starting the task with + insted of -
        As that would be even more minimal. But let's see. Currently no 
        prefix `-` is required to start a line, needing to add that seems to suck?
        
        Maybe it would make integration into an operational transport enabled live 
        markdown editor more simple? Will have to see.
        """
    
    
