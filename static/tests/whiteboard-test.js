Vue.config.productionTip = false // unit tests != production, but still annyoing

import whiteboard from '../whiteboard.js'
const Whiteboard = Vue.extend(whiteboard)

describe('Whiteboard', () => {
    
    function task(overrides) {
        if ( ! task.count) {
            task.count = 0
        }
        let standard = {
            line:'',
            id: task.count++,
            status:'new',
            children:[],
            contexts: [],
        }
        return Object.assign({}, standard, overrides)
    }
	
	function socketMock() {
		return {}
	}
    
    it('smokes', () => {
        const vm = new Whiteboard({ propsData: { rootTask: task({line: 'task title'}), socket: socketMock() }}).$mount()
        expect(vm.$el.title).toBe('task title')
        expect(vm.$el.className).toBe('whiteboard')
    })

    it('should not explode with an empty task', () => {
        const vm = new Whiteboard({ propsData: { rootTask: {}, socket: socketMock() }}).$mount()
    })
    
    describe('data access functions', () => {
        
        it('should access children by status', () => {
            let board = new Whiteboard({ propsData: { rootTask: task(), socket: socketMock() } }).$mount()
            expect(board.childrenInStatus(task(), 'new')).toEqual([])
            expect(board.childrenInStatus(task(), 'doing')).toEqual([])
            expect(board.childrenInStatus(task(), 'done')).toEqual([])
            
            expect(board.childrenInStatus(task({children:[task()]}), 'new').length).toBe(1)
            expect(board.childrenInStatus(task({children:[task(), task()]}), 'new').length).toBe(2)
        })
    })
    
    describe('rendering', () => {
        
        beforeEach(function() {
            let data = {
                propsData: {
                    rootTask: task({
                        line: 'root task',
                        children: [
                            task({ children: [task(), task({ status: 'doing' })] }),
                            task(),
                        ],
                    }),
                    socket: socketMock()
                }
            }
            this.board = new Whiteboard(data).$mount()
        })
        
        describe('header', () => {
            
            it('should render the title', function() {
                expect(this.board.$('.header h1').text()).toContain('root task')
            })
            
            it('should render column headers', function() {
                expect(this.board.$('.header .column-headers .column.header.new').text()).toContain('new')
            })
            it('should render the number of tasks in each status', async function() {
                expect(this.board.$('.header .column-headers .column.header.new').text()).toContain('1')
                this.board.task.children[0].children.push(task())
                await Vue.nextTick().then(() => {
                    expect(this.board.$('.header .column-headers .column.header.new').text()).toContain('2')
                })
            })
            
            it('should only show the unknown column if neccessary', async function() {
                expect(this.board.$('.header .column-headers .column.header.unknown').length).toBe(0)
                this.board.task.children[0].children.push(task({ status: 'unknown' }))
                await Vue.nextTick().then(() => {
                    expect(this.board.$('.header .column-headers .column.header.unknown').text()).toContain('unknown 1')
                })
            })
            
            it('should show breadcrumbs', async function() {
                expect(this.board.$('.header .breadcrumb-item').length).toBe(1)
                expect(this.board.$('.header .breadcrumb-item').text()).toContain('root task')
                this.board.breadcrumbs.push(task({ line: 'second task'}))
                await Vue.nextTick().then(() => {
                    expect(this.board.$('.header .breadcrumb-item').length).toBe(2)
                    expect(this.board.$('.header .breadcrumb-item').text()).toContain('root task')
                })
            })
        })
        
        describe('task rows', () => {
            
            it('should render one row per task', function() {
                expect(this.board.$('.task').length).toBe(2)
            })
            
            it('should show task metadata')
            
            it('should render child-tasks in the correct row', async function() {
                expect(this.board.$('.status.new .subtask').length).toBe(1)
                expect(this.board.$('.status.doing .subtask').length).toBe(1)
                
                this.board.task.children[0].children[1].status = 'new'
                await Vue.nextTick().then(() => {
                    expect(this.board.$('.status.new .subtask').length).toBe(2)
                    expect(this.board.$('.status.doing .subtask').length).toBe(0)
                })
            })
            
            it("should update only status, not position when doing drag'n'drop", async function() {
                // how do I trigger the dragdrop programmatically? 
                // I can call the event all right, but the trick is to see that <draggable> doesn't interfere
                // could do it via selenium, but...
            })
        })
    })
})
