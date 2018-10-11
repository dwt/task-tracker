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

def id_generator():
    if not hasattr(id_generator, 'counter'):
        id_generator.counter = 0
    
    id_generator.counter -= 1
    return id_generator.counter

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
            (?:(?P<simple>[\-\w]+)
            |\'(?P<single>[\-\w\s]+)\'
            |\"(?P<double>[\-\w\s]+)\")
        ''', flags=re.X
        )
    
    def __init__(self, line=None, body=None):
        self.line = line or ''
        self.body = body or ''
        # REFACT lazy create
        self.children = FilterableList(self)
        # cannot ensure_id() here, as that would turn all body lines into tasks
    
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
    
    def ensure_id(self):
        if self.is_virtual:
            return
        
        # REFACT would be nice to use only self.json = dict(...) to modify the line
        # self.json = dict(id=id_generator())
        if not 'id' in self.tags:
            self.line += f' id:{id_generator()!s}'
    
    @property
    def id(self):
        assert not self.is_virtual, 'cannot ask for id of virtual task, as it means the insertion code has a bug somewhere' 
        
        self.ensure_id()
        
        return self.tags['id']
    
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
        if self.is_virtual:
            return dict()
        
        return dict(
            line=self.line, 
            id=self.id,
            body=self.body,
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
        
        To make this method viable, it probably needs that the client files
        minimal update bundles, that are then applied as an update that only changes one aspect?
        Not sure how this is to work with child tasks.
        """
        # REFACT Gnarly code, not sure how to write this more beautifull
        
        if 'line' in json:
            self.line = json['line']
        
        if 'body' in json:
            self.body = json['body']
        
        if 'status' in json:
            json.setdefault('tags', {})['status'] = json.get('status')
        
        if 'id' in json:
            json.setdefault('tags', {})['id'] = json.get('id')
        
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
        
        self.ensure_id()
    
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

