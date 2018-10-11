from todotxt import *

from pyexpect import expect
from unittest import TestCase

class TodoTest(TestCase):
    
    def setUp(self):
        super().setUp()
        id_generator.counter = 0
    
    def test_simple(self):
        expect(str(Todo(''))) == ''
        
        simple = 'I am a simple todo item id:1'
        todo = Todo(simple)
        expect(str(todo)) == simple
    
    def test_self_assigned_id(self):
        todo = Todo(line='foo bar:baz')
        todo.ensure_id()
        expect(todo.line) == 'foo bar:baz id:-1'
        expect(todo.id) == '-1'
        
        todo = Todo('foo bar:baz')
        expect(todo.json).has_subdict(id='-2')
        expect(todo.line) == 'foo bar:baz id:-2'
    
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
        expect(Todo('foo foo:bar sprint:"fnordy fnord roughnecks"').tags).has_subdict(sprint="fnordy fnord roughnecks", foo='bar')
        expect(Todo("foo foo:bar sprint:'fnordy fnord roughnecks'").tags).has_subdict(sprint="fnordy fnord roughnecks", foo='bar')
    
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
        todo = Todo(line='foo id:3', body='        foo\n        bar')
        expect(todo.body) == '        foo\n        bar'
        
        todo.add_body_line('        baz')
        expect(todo.body) == '        foo\n        bar\n        baz'
        
        expect(str(todo)) == dedent('''
            foo id:3
                    foo
                    bar
                    baz
            ''').strip()

    def test_to_json(self):
        expect(Todo('foo id:1').json) == dict(line='foo id:1', body='', id='1', status='new',
            is_done=False, contexts=[], projects=[], tags={'id': '1'}, children=[])
        expect(Todo('x foo @context tag:value, +project id:1 status:doing').json).has_subdict(
            line='x foo @context tag:value, +project id:1 status:doing', 
            id='1', is_done=True, contexts=['context'], status='doing',
            projects=['project'], tags={'tag': 'value', 'id': '1', 'status': 'doing' }, 
        )
        expect(Todo('foo status:done').json).has_subdict(is_done=True)

        todo = Todo('')
        todo.json = dict(
            line='foo id:1 removed:tag', 
            body='      baz quoox',
            is_done=True, 
            tags={'id':'1', 'key':'value', 'status':'done'}, 
            children=[],
        )
        expect(todo.is_done).is_true()
        expect(todo.tags) == {'id':'1', 'key':'value'}
        expect(todo.line) == 'x foo id:1 key:value'
        expect(todo.body) == '      baz quoox'

        todo = Todo('')
        todo.json = dict(line='x foo id:1', is_done=False)
        expect(todo.line) == 'foo id:1'
    
    def test_from_json(self):
        todo = Todo('task id:1')
        # Currently have no plan to update ids from client
        # todo.json = dict(id=-3)
        # expect(todo.line) == 'task id:-3'
        
        todo.json = dict(status='doing', id='1')
        expect(todo.line) == 'task id:1 status:doing'
        
        # todo.json = dict(status='done')
        # expect(todo.line) == 'x task'
    
    def test_ensure_tasks_always_have_an_id(self):
        expect(lambda: Todo().id).to_raise(AssertionError)
        expect(Todo('fnord').id) == '-1'
    

from textwrap import dedent
class MultipleTodosTest(TestCase):
    
    def setUp(self):
        super().setUp()
        id_generator.counter = 0

    def test_multi_lines(self):
        lines = dedent("""
        first id:1
        x second id:2
        third id:2346 sprint:'fnordy fnord roughnecks'
        """)
        todo = Todo.from_lines(lines)
        
        expect(todo.is_virtual).is_true()
        expect(todo.children).has_length(3)
        expect(str(todo.children[0])) == 'first id:1'
        expect(todo.children[1].is_done).is_true()
        expect(todo.children[2].tags) == { 'id': '2346', 'sprint': 'fnordy fnord roughnecks' }
        expect(str(todo)) == lines.strip()
    
    def test_sub_tasks(self):
        lines = dedent("""
        first id:1
          x second id:2
          third id:2346 sprint:'fnordy fnord roughnecks'
        """)
        parent = Todo.from_lines(lines)
        
        expect(parent.line) == 'first id:1'
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
            parent id:1
                child id:2
        '''))
        expect(parent.json.get('children')[0]).has_subdict(line='    child id:2')


        todo = Todo.from_lines(dedent('''
            parent id:1
                new1 id:2
                new2 @phone id:3
                doing status:doing id:4
                x done1 id:5
        '''))
        
        recreated_todo = Todo()
        recreated_todo.json = json.loads(json.dumps(todo.json))
        
        expect(recreated_todo.line) == todo.line
        for index, child in enumerate(todo.children):
            expect(recreated_todo.children[index].line) == child.line
    
    def test_empty_lines_are_attached_as_body_to_tasks(self):
        # Sadly dedent will kill _all_ whitespace in empty lines, so can't use it here
        lines = dedent("""\
        foo id:1
            bar id:2
            
            baz id:3
        
        quoox id:4
        """).strip()
        # dedent kills all spaces from empty lines!
        
        virtual = Todo.from_lines(lines)
        foo = virtual.children[0]
        expect(foo.line) == 'foo id:1'
        expect(foo.children).has_length(2)
        
        bar = foo.children[0]
        expect(bar.line) == '    bar id:2'
        expect(bar.body) == ''
        
        baz = foo.children[1]
        expect(baz.line) == '    baz id:3'
        expect(baz.body) == ''
    
    def test_expanded_stories_eat_intermitent_empty_lines(self):
        todo = Todo.from_lines('task\n        double indented body')
        expect(todo.body) == '        double indented body'
        
        todo = Todo.from_lines('task\n        body\n\n        eats empty lines')
        expect(todo.body) == '        body\n\n        eats empty lines'
        
        todo = Todo.from_lines('task\n        body\n    \n            \n        eats whitespace lines')
        expect(todo.body) == '        body\n    \n            \n        eats whitespace lines'
        
    
    def _test_expanded_stories_can_be_collapsed(self):
        r"""
        Not sure at all that this is a good idea. How do I want to represent collapsed stories?
        How do I deal with the different storage formats that this requires? Because I need to decide
        wether to save the expanded version to keep it or wether to give out the condensed version.
        
        
        
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
    
    
