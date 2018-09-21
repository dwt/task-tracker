#!/usr/bin/env python3


import re
from functools import wraps
import fluentpy as _
import inspect
import json

def tupelize(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        return tuple(method(*args, **kwargs))
    return wrapper

class FilterableList(list):
    def __init__(self, parent):
        super()
        self._parent = parent
    
    @property
    def tagged(self):
        return self
    
    # REFACT consider putting them on their own class, to have a smaller interface

    @property
    @tupelize
    def new(self):
        candidates = self._parent.children_tagged('status:new') \
            + self._parent.children_not_tagged('status:')
        done = self._parent.children.tagged.done
        for child in self:
            if child in candidates and child not in done:
                yield child
    
    @property
    def doing(self):
        return self._parent.children_tagged('status:doing')
    
    @property
    @tupelize
    def done(self):
        done_tasks = _(self._parent.children).filter(_.each.is_done)._ + self._parent.children_tagged('status:done')
        for child in self._parent.children:
            if child in done_tasks:
                yield child
    
    @property
    @tupelize
    def unknown(self):
        known_tagged = self.new + self.doing + self.done
        for child in self:
            if child not in known_tagged:
                yield child

class Todo:
    
    "int: how many spaces is one level of indentation."
    INDENT = 4
    
    # TODO consider to retain offsets of all matches, so they can easily be used for a highlighter
    
    class REGEX:
        # TODO require whitespace at beginning
        IS_DONE = re.compile(r'^\s*(x)\s')
        CONTEXTS = re.compile(r'@(\w+)')
        PROJECTS = re.compile(r'\+(\w+)')
        # TODO consider allowing escaped ' and " in the strings. Perhaps easier to allow ''' and """.
        TAGS = re.compile(r'''
            (\w+):
            (?:(?P<simple>\w+)
            |\'(?P<single>[\w\s]+)\'
            |\"(?P<double>[\w\s]+)\")
        ''', flags=re.X
        )
    
    def __init__(self, line=None, body=None):
        self.line = line or ''
        self.body = body or ''
        self.children = FilterableList(self)
    
    @classmethod
    def from_lines(cls, lines):
        """Tasks become children of Tasks when they are indented by two spaces after another task.
        """
        todos = []
        for line in lines.strip().split('\n'):
            todo = Todo(line)
            if todo.has_prefix() or todo.is_virtual:
                todos[-1].add_child(todo)
            else:
                todos.append(todo)
        
        if len(todos) == 1:
            return todos[0]
        else:
            virtual_todo = Todo()
            virtual_todo.children.extend(todos)
            return virtual_todo
        
    def __str__(self):
        lines = list(map(str, self.children))
        
        if not self.is_virtual:
            lines.insert(0, self.line)
        
        if self.body:
            lines.append(self.body)
        
        return '\n'.join(lines)
    
    def __repr__(self):
        return f'<Todo(line={self.line!r}, body={self.body!r} children={self.children!r})>'
    
    @property
    def is_virtual(self):
        return self.line.strip() == ''
    
    @property
    def id(self):
        return self.tags.get('id', '')
    
    # REFACT consider to remove, self.status should be easier to work with
    @property
    def is_done(self):
        return bool(self.REGEX.IS_DONE.match(self.line)) \
            or self.has_tags('status:done')
    
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
    def status(self):
        # FIXME find a way to make these status configurable
        # REFACT consider using is: tag for status because of shortness
        if self.has_tags('status:'):
            status = self.tags['status']
            if status in 'new doing done'.split():
                return status
            else:
                return 'unknown'
        
        if self.is_done:
            return 'done'
        
        if self.has_no_tags('status:'):
            return 'new'
    
    @property
    def prefix(self):
        return re.match(r'^(\s*)', self.line).groups()[0] or ''
    
    def has_prefix(self):
        return len(self.prefix) > 0
    
    @property
    def json(self):
        return dict(
            line=self.line, 
            body=self.body,
            id=self.id,
            is_done=self.is_done, 
            status=self.status,
            contexts=self.contexts, 
            projects=self.projects, 
            tags=self.tags, 
            children=[child.json for child in self.children],
        )
    
    @json.setter
    def json(self, json):
        """Updates the line from the json properties
        
        Currently very basic, in that it only really updates the status
        Everything else needs to happen later
        TODO allow updating all parts via json
        """
        # REFACT Gnarly code, not sure how to write this more beautifull
        
        if json.get('status', ''):
            json.setdefault('tags', {})['status'] = json.get('status')
        
        if json.get('tags', {}):
            for existing_key, existing_value in self.tags.items():
                if existing_key not in json.get('tags', {}) or existing_value != json.get('tags', {}).get(existing_key):
                    self.edit(remove=f'{existing_key}:{existing_value}') # FIXME handle quoting
            
            existing_tags = self.tags
            for key, value in json.get('tags', {}).items():
                if key not in existing_tags:
                    self.line += f' {key}:{value}' # FIXME handle quoting
        
            # normalize status tags
            if self.has_tags('status:new'):
                self.edit(remove='status:new')
            if self.has_tags('status:done'):
                json['is_done'] = True
        
        if json.get('is_done', False) or json.get('tags', {}).get('state') == 'done':
            if self.has_tags('status:done'):
                self.edit(remove='status:done')
            if not self.is_done:
                self.line = re.sub(r'(^\s*)(.*$)', r'\1x \2', self.line)
        
        if not json.get('is_done', False) and self.is_done:
                self.line = re.sub(r'(^\s*)x\s+\b(.*$)', r'\1\2', self.line)
        
        if json.get('children', []):
            json_children = json.get('children', [])
            
            if len(json_children) > len(self.children):
                for _ in range((len(json_children) - len(self.children))):
                    self.children.append(Todo())
            elif len(json_children) < len(self.children):
                self.children = self.children[:len(json_children)]
            
            for child, child_json in zip(self.children, json_children):
                child.json = child_json
    
    def edit(self, remove=None, remove_re=None, replace_with=' '):
        if remove is not None:
            self.line, ignored = re.subn(r'\s+' + re.escape(remove) + r'(\s+|$)', replace_with, self.line)
        if remove_re is not None:
            self.line, ignored = re.subn(remove_re, replace_with, self.line)
        self.line = self.line.rstrip()
    
    def has_children(self):
        return len(self.children) > 0
    
    def is_body_of(self, other):
        if other.has_children():
            return False
        
        return self.is_virtual or self.is_twice_more_indented_than(other)
    
    def is_child_or_body_of(self, other):
        return self.is_more_indented_than(other) or self.is_virtual
    
    # REFACT rename add_child_or_body
    def add_child(self, child):
        if child.is_body_of(self):
            self.add_body_line(child.line)
        elif self.has_children() and child.is_child_or_body_of(self.children[-1]):
            self.children[-1].add_child(child)
        else:
            self.children.append(child)
    
    @property
    def indentation_level(self):
        return (len(self.prefix) // self.INDENT)
    
    def is_more_indented_than(self, other):
        return self.indentation_level \
            > other.indentation_level
    
    def is_twice_more_indented_than(self, other):
        return self.indentation_level \
            > 1 + other.indentation_level
    
    @tupelize
    def children_tagged(self, *tags):
        for child in self.children:
            if child.has_tags(*tags):
                yield child
    
    @tupelize
    def children_not_tagged(self, *tags):
        "Does not have any of the tags given"
        for child in self.children:
            if child.has_no_tags(*tags):
                yield child
    
    def has_tags(self, *tags):
        "Accepts 'tag:' if the value doesn't matter or 'tag:foo' for specific values"
        for tag in tags:
            key, value = tag.split(':')
            if value == '': # value doesn't matter:
                if key not in self.tags:
                    return False
            else:
                if self.tags.get(key, None) != value:
                    return False
        return True
    
    def has_no_tags(self, *tags):
        "Accepts 'tag:' if the value doesn't matter or 'tag:foo' for specific values"
        for tag in tags:
            if self.has_tags(tag):
                return False
        
        return True
    
    def add_body_line(self, line):
        if '' == self.body:
            self.body = line
            return
        
        self.body += '\n' + line


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
        expect(Todo('fnord status:done').is_done).is_true()
    
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
        expect(Todo('foo').has_tags('tag:')).is_false()
        expect(Todo('foo bar:baz').has_tags('bar:')).is_true()
        expect(Todo('foo bar:baz').has_tags('bar:quoox')).is_false()
        expect(Todo('foo bar:baz').has_tags('bar:baz')).is_true()

        expect(Todo('foo').has_no_tags('tag:')).is_true()
        expect(Todo('foo bar:baz').has_no_tags('bar:')).is_false()
        expect(Todo('foo bar:baz').has_no_tags('bar:quoox')).is_true()
        expect(Todo('foo bar:baz').has_no_tags('bar:baz')).is_false()
    
    def test_tags_with_spaces(self):
        expect(Todo('foo foo:bar sprint:"fnordy fnord roughnecks"').tags) == { 'sprint': "fnordy fnord roughnecks", 'foo':'bar' }
        expect(Todo("foo foo:bar sprint:'fnordy fnord roughnecks'").tags) == { 'sprint': "fnordy fnord roughnecks", 'foo':'bar' }
    
    def test_status_property(self):
        expect(Todo().status) == 'new'
        expect(Todo('foo').status) == 'new'
        expect(Todo('x foo').status) == 'done'
        expect(Todo('foo status:doing').status) == 'doing'
        expect(Todo('foo status:something').status) == 'unknown'
    
    def test_empty_todo_knows_it_is_virtual(self):
        todo = Todo()
        expect(todo.is_virtual) == True
    
    def test_body(self):
        todo = Todo(line='foo', body='        foo\n        bar')
        expect(todo.body) == '        foo\n        bar'
        
        todo.add_body_line('        baz')
        expect(todo.body) == '        foo\n        bar\n        baz'
        
        expect(str(todo)) == dedent('''
            foo
                    foo
                    bar
                    baz
            ''').strip()

    def test_to_json(self):
        expect(Todo('foo').json) == dict(line='foo', body='', id='', status='new',
            is_done=False, contexts=[], projects=[], tags={}, children=[])
        expect(Todo('x foo @context tag:value, +project id:1 status:doing').json).has_subdict(
            line='x foo @context tag:value, +project id:1 status:doing', 
            id='1', is_done=True, contexts=['context'], status='doing',
            projects=['project'], tags={'tag': 'value', 'id': '1', 'status': 'doing' }, 
        )
        expect(Todo('foo status:done').json).has_subdict(is_done=True)

        todo = Todo('')
        todo.json = dict(
            line='foo removed:tag', 
            body='      baz quoox',
            is_done=True, 
            tags={'key': 'value', 'status': 'done'}, 
            children=[],
        )
        expect(todo.is_done).is_true()
        expect(todo.tags) == {'key': 'value'}
        expect(todo.line) == 'x foo key:value'
        expect(todo.body) == '      baz quoox'

        todo = Todo('')
        todo.json = dict(line='x foo', is_done=False)
        expect(todo.line) == 'foo'
    
    def test_from_json(self):
        todo = Todo('task')
        # Currently have no plan to update ids from client
        # todo.json = dict(id=-3)
        # expect(todo.line) == 'task id:-3'
        
        todo.json = dict(status='doing')
        expect(todo.line) == 'task status:doing'
        
        # todo.json = dict(status='done')
        # expect(todo.line) == 'x task'

from textwrap import dedent
class MultipleTodosTest(TestCase):
    
    def test_multi_lines(self):
        lines = dedent("""
        first
        x second
        third id:2346 sprint:'fnordy fnord roughnecks'
        """)
        todo = Todo.from_lines(lines)
        
        expect(todo.is_virtual).is_true()
        expect(todo.children).has_length(3)
        expect(str(todo.children[0])) == 'first'
        expect(todo.children[1].is_done).is_true()
        expect(todo.children[2].tags) == { 'id': '2346', 'sprint': 'fnordy fnord roughnecks' }
        expect(str(todo)) == lines.strip()
    
    def test_sub_tasks(self):
        lines = dedent("""
        first
          x second
          third id:2346 sprint:'fnordy fnord roughnecks'
        """)
        parent = Todo.from_lines(lines)
        
        expect(parent.line) == 'first'
        expect(str(parent)) == lines.strip()
        expect(parent.children[0].is_done).is_true()
        expect(parent.children[1].tags) == { 'id': '2346', 'sprint': 'fnordy fnord roughnecks' }
    
    def test_sub_sub_tasks(self):
        parent = Todo.from_lines(dedent("""
        first
          x second
            third id:2346 sprint:'fnordy fnord roughnecks'
          fourth +project1
        """))
        
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
        """))
        
        expect(parent.line).contains('parent')
        doing = parent.children_tagged('status:doing')
        expect(doing).has_length(2)
        expect(doing[0].line).contains('child1')
        expect(doing[1].line).contains('child3')
        
        waiting = parent.children_not_tagged('status:doing', 'status:done')
        expect(waiting).has_length(1)
        expect(waiting[0].line).contains('child2')
    
    def test_access_relevant_task_states_as_properties(self):
        parent = Todo.from_lines(dedent('''
            parent
                new1
                new2 status:new
                unknown1 status:something
                unknown2 status:something
                doing status:doing
                x done1
                x done2 status:done
        '''))
        
        expect(parent.line).contains('parent')
        expect(parent.children.tagged.new).has_length(2)
        expect(parent.children.tagged.new[0].line).contains('new1')
        expect(parent.children.tagged.new[1].line).contains('new2')

        expect(parent.children.tagged.doing).has_length(1)
        expect(parent.children.tagged.done).has_length(2)

        expect(parent.children.tagged.unknown).has_length(2)
    
    def test_json_serialization(self):
        parent = Todo.from_lines(dedent('''
            parent
                child
        '''))
        expect(parent.json.get('children')[0]).has_subdict(line='    child')


        todo = Todo.from_lines(dedent('''
            parent
                new1
                new2 @phone
                doing status:doing
                x done1
        '''))
        
        recreated_todo = Todo()
        recreated_todo.json = json.loads(json.dumps(todo.json))
        
        expect(recreated_todo.line) == todo.line
        for index, child in enumerate(todo.children):
            expect(recreated_todo.children[index].line) == child.line
    
    def test_expanded_stories_eat_empty_lines(self):
        # Sadly dedent will kill _all_ whitespace in empty lines, so can't use it here
        lines = dedent("""\
        foo
            bar
            
            baz
        
        quoox
        """).strip()
        
        virtual = Todo.from_lines(lines)
        foo = virtual.children[0]
        bar = foo.children[0]
        # REFACT what should the body be here?
        # expect(bar.body) == '    '
        
        baz = foo.children[1]
        expect(baz.body) == ''
    
    def test_expanded_stories_eat_twice_indented_lines(self):
        todo = Todo.from_lines(dedent('''
        foo
                foo body
                
                and more body
            bar
                    bar content
        '''))
        expect(todo.body) == '        foo body\n\n        and more body'
    
    def test_expanded_stories_can_be_collapsed(self):
        """
        TODO
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
    
    
