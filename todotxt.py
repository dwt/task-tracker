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

def json_dumps(something):
    def serialize_with__to_json__(an_object):
        if '__to_json__' not in dir(an_object) or not inspect.ismethod(an_object.__to_json__):
            raise TypeError()
        
        return an_object.__to_json__()
    
    return json.dumps(something, default=serialize_with__to_json__)


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
    
    # TODO retain offsets of all matches, so they can easily be used for a highlighter
    
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
    
    def __init__(self, line):
        self.line = line
        self.children = FilterableList(self)
    
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
    def prefix(self):
        return re.match(r'^(\s*)', self.line).groups()[0] or ''
    
    def has_prefix(self):
        return len(self.prefix) > 0
    
    def __to_json__(self):
        return dict(
            line=self.line, 
            is_done=self.is_done, 
            contexts=self.contexts, 
            projects=self.projects, 
            tags=self.tags, 
            children=dict(
                new=_(self.children.tagged.new).map(_.each.json)._,
                unknown=_(self.children.tagged.unknown).map(_.each.json)._,
                doing=_(self.children.tagged.doing).map(_.each.json)._,
                done=_(self.children.tagged.done).map(_.each.json)._,
            ),
        )
    json = property(__to_json__)
    
    @json.setter
    def json(self, json):
        "Updates the line from the json properties"
        # REFACT Gnarly code, not sure how to write this more beautifull
        self.line = json.get('line', '')

        if json.get('projects', []):
            for existing_project in self.projects:
                if existing_project not in json.get('projects', []):
                    self.edit(remove=f'+{existing_project}')
            
            existing_projects = self.projects
            for project in json.get('projects', []):
                if project not in existing_projects:
                    self.line += f' +{project}'
        
        if json.get('contexts'):
            for existing_context in self.contexts:
                if existing_context not in json.get('contexts', []):
                    self.edit(remove=f'@{existing_context}')
                
                existing_contexts = self.contexts
                for context in json.get('contexts', []):
                    if context not in existing_contexts:
                        self.line += f' @{context}'
        
        if json.get('tags', {}):
            for existing_key, existing_value in self.tags.items():
                if existing_key not in json.get('tags', {}) or existing_value != json.get('tags', {}).get(existing_key):
                    self.edit(remove=f'{existing_key}:{existing_value}') # FIXME handle quoting
            
            existing_tags = self.tags
            for key, value in json.get('tags', {}).items():
                if key not in existing_tags:
                    self.line += f' {key}:{value}' # FIXME handle quoting
        
        if json.get('is_done', False) or json.get('tags', {}).get('state') == 'done':
            if self.has_tags('state:done'):
                self.edit(remove='state:done')
            if not self.is_done:
                self.line = re.sub(r'(^\s*)(.*$)', r'\1x \2', self.line)
        
        if not json.get('is_done', False) and self.is_done:
                self.line = re.sub(r'(^\s*)x\s+\b(.*$)', r'\1\2', self.line)
    
    def edit(self, remove=None, remove_re=None, replace_with=' '):
        if remove is not None:
            self.line, ignored = re.subn(r'\s+' + re.escape(remove) + r'(\s+|$)', replace_with, self.line)
        if remove_re is not None:
            self.line, ignored = re.subn(remove_re, replace_with, self.line)
        self.line = self.line.rstrip()
    
    def has_children(self):
        return len(self.children) > 0
    
    def add_child(self, child):
        if self.has_children() and child.is_more_indented_than(self.children[-1]):
            self.children[-1].add_child(child)
        else:
            self.children.append(child)
    
    def is_more_indented_than(self, other):
        return len(self.prefix) > len(other.prefix)
    
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
    
    def test_to_json(self):
        expect(Todo('foo').json) == dict(line='foo', is_done=False, contexts=[], projects=[], tags={}, 
            children=dict(new=tuple(), unknown=tuple(), doing=tuple(), done=tuple()))
        expect(Todo('x foo @context tag:value, +project').json).has_subdict(
            line='x foo @context tag:value, +project', 
            is_done=True, contexts=['context'], 
            projects=['project'], tags={'tag': 'value'}, 
        )
        expect(Todo('foo status:done').json).has_subdict(is_done=True)

        todo = Todo('')
        todo.json = dict(
            line='foo @removed_context removed:tag +removed_project', 
            is_done=True, 
            contexts=['context'], 
            projects=['project'], 
            tags={'key': 'value', 'state': 'done'}, 
            children={},
        )
        expect(todo.is_done).is_true()
        expect(todo.contexts) == ['context']
        expect(todo.projects) == ['project']
        expect(todo.tags) == {'key': 'value'}
        expect(todo.line) == 'x foo +project @context key:value'

        todo = Todo('')
        todo.json = dict(line='x foo', is_done=False)
        expect(todo.line) == 'foo'

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
        '''))[0]

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
        '''))[0]
        expect(parent.json.get('children').get('new')[0]).has_subdict(line='    child')


        todos = Todo.from_lines(dedent('''
            parent
                new1
                new2 status:new @phone
                doing status:doing
                x done1
        '''))

        expect(json_dumps(todos)) \
            == json.dumps([todos[0].json])

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
    
    
