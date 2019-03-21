#!/usr/bin/env python3

"""
This roughly follows the todotxt standard to describe hierarchies of todo items in a flat text file format.

For example
```
This is a sprint
    This is a story
        This is a (new) task in that story
        This task is in progress status:doing
        x This task is done
        This task is assigned to @martin
        This Task has it's description included
                I'm part of the description
                
                Which can be multi line of course
            It can also have child tasks like this
```

You can assign whatever meaning you want to the nesting, So it might be Sprint / Story / Task 
for you, or rather Milestone / Epic / Task - whatever you need.

The text format is not yet set in stone, as I'm still trying to find out what works best.

Planning for this project is supposed to happen in the todo.txt file in this directory. Look there for inspiration.

Some syntax ideas that are not yet very very final
- Would it be better to use the established syntax of #234 as a ticket id?
- Is there a better / cleaner way to display the task status? Currently its nothing for 
    `new` `status:doing` and `x ...` for done tasks. I could think about going :doing, or *doing* or whatever

"""

import re
from functools import wraps
import uuid

import fluentpy as _
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

# TODO consider to retain offsets of all matches, so they can easily be used for a highlighter
class Todo:
    
    "int: how many spaces is one level of indentation."
    INDENT = 4
    
    class Parser:
        IS_DONE = re.compile(r'^\s*(x)\s')
        ID = re.compile(r'#(\d+)')
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
        
        @classmethod
        def is_whitespace(cls, line):
            return line.strip() == ''
        
        @classmethod
        def indentation_level(cls, line):
            if line is None:
                return -1
            
            return len(cls.prefix(line)) // Todo.INDENT
        
        @classmethod
        def prefix(cls, line):
            return re.match(r'^(\s*)', line).groups()[0] or ''
    
    def __init__(self, line=None, body=None):
        self.line = line
        self.body = body
        # REFACT lazy create
        self.children = FilterableList(self)
    
    @classmethod
    def from_lines(cls, lines):
        """Tasks become children of Tasks when they are indented by two spaces after another task.
        """
        root = Todo(line=None, body=None)
        for line in lines.split('\n'):
            root.append_body_or_child(line)
        
        if root.body or 1 != len(root.children):
            return root
        
        return root.children[0]
    
    def append_body_or_child(self, line):
        current_indentation_level = self.Parser.indentation_level(self.line)
        indentation_level = self.Parser.indentation_level(line)
        is_body_line = indentation_level >  1 + current_indentation_level
        
        if self.Parser.is_whitespace(line) or is_body_line:
            if self.has_children():
                return self.children[-1].append_body_or_child(line)
            else:
                return self.add_body_line(line)
        else:
            return self.children.append(Todo(line))
    
    # REFACT consider inlining
    @property
    def is_virtual(self):
        return self.line is None
    
    def add_body_line(self, line):
        if self.body is None:
            self.body = line
            return
        
        self.body += '\n' + line
    
    def __str__(self):
        lines = []
        
        if self.line is not None:
            lines.append(self.line)
        
        if self.body is not None:
            lines.append(self.body)
        
        lines.extend(map(str, self.children))
        
        return '\n'.join(lines)
    
    def __repr__(self):
        return f'<Todo(line={self.line!r}, body={self.body!r} children={self.children!r})>'
    
    @property
    def uuid(self):
        if not hasattr(self, '_uuid'):
            self._uuid = str(uuid.uuid4())
            
        return self._uuid
    
    # REFACT this should really use a dict as cache or as primary lookup structure
    def task_by_uuid(self, uuid):
        if self.uuid == uuid:
            return self
        
        for child in self.children:
            child_or_none = child.task_by_uuid(uuid)
            if child_or_none is not None:
                return child_or_none
        
    
    @property
    def id(self):
        ids = self.Parser.ID.findall(self.line)
        assert len(ids) in (0,1), 'Detected more than one ID for this task'
        if 0 == len(ids):
            return
        return ids[0]
    
    # REFACT consider to remove, self.status should be easier to work with
    @property
    def is_done(self):
        return bool(self.Parser.IS_DONE.match(self.line)) \
            or self.has_tags('status:done')
    
    @property
    def contexts(self):
        return self.Parser.CONTEXTS.findall(self.line)
    
    @property
    def projects(self):
        return self.Parser.PROJECTS.findall(self.line)
    
    @property
    def tags(self):
        if not self.line:
            return dict()
        matches = self.Parser.TAGS.findall(self.line)
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
    
    def has_children(self):
        return len(self.children) > 0
    
    @property
    def json(self):
        if self.is_virtual:
            return dict(
                body=self.body,
                children=[child.json for child in self.children],
            )
        
        return dict(
            uuid=self.uuid,
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
    
    def on_operation(self, operation_name, **json):
        if operation_name in ['change_tag']:
            self.json = json
        elif operation_name in ['add_child']:
            child = Todo()
            child.json = json
            self.children.append(child)
        else:
            assert False, f'operation {operation_name} is not supported'
    
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
            if json['id'] and not self.id:
                self.line += f' #{json["id"]}'
            else:
                self.edit(remove=f'#{self.id}', replace_with=f" #{json['id']}")
        
        if json.get('tags', {}) or self.tags:
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
                self.edit(remove='status:done')
                json['is_done'] = True
        
        # REFACT Could be that it is signifficantly easier to just reflect the status 
        # as it's own syntactic ting instead of hijacking tags
        if 'is_done' in json:
            if json['is_done'] and not self.is_done:
                self.line = re.sub(r'(^\s*)(.*$)', r'\1x \2', self.line)
            elif not json['is_done'] and self.is_done:
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
    

