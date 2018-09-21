Vue.config.productionTip = false; // unit tests != production, but still annyoing

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
        }
        return Object.assign({}, standard, overrides)
    }
    
    beforeAll(async () => {
        // this is how modules need to be imported in jasmine tests
        // as tests cannot themselves be es6 modules (yet?)
        // my understanding is that if they are modules, then they are executed 
        // _later_ at a time when jasmine has already closed registration for it's testsuite
        // which means they are simply not found
        whiteboard = (await import('../whiteboard.js')).default
        Whiteboard = Vue.extend(whiteboard)
    })
    
    it('smoke', () => {
        const vm = new Whiteboard({ propsData: { rootTask: task({line: 'task title'}) }}).$mount()
        expect(vm.$el.title).toBe('task title')
        expect(vm.$el.className).toBe('whiteboard')
    })

    it('should not explode with an empty task', () => {
        const vm = new Whiteboard({ propsData: { rootTask: {} }}).$mount()
    })
    
    describe('accessing children with specific tags', () => {
        
        it('should access children by status', () => {
            let board = new Whiteboard({ propsData: { rootTask: task() } }).$mount()
            expect(board.childrenInStatus(task(), 'new')).toEqual([])
            expect(board.childrenInStatus(task(), 'doing')).toEqual([])
            expect(board.childrenInStatus(task(), 'done')).toEqual([])
            
            expect(board.childrenInStatus(task({children:[task()]}), 'new').length).toBe(1)
            expect(board.childrenInStatus(task({children:[task(), task()]}), 'new').length).toBe(2)
        })
    })
    
    describe('rendering tasks', () => {
        beforeEach(function() {
            let data = {
                propsData: {
                    rootTask: task({
                        line: 'fresh task',
                        children: [
                            task({ children: [task(), task({ status: 'doing' })] }),
                            task(),
                        ],
                    })
                }
            }
            this.board = new Whiteboard(data).$mount()
        })
        
        it('should render the title', function() {
            expect(this.board.$el.querySelector('.header h1').textContent).toContain('fresh task')
        })
        
        it('should render column headers', function() {
            expect(this.board.$el.querySelector('.header .column-headers .column.header.new').textContent).toContain('new')
        })
        it('should render the number of tasks in each status', async function() {
            expect(this.board.$el.querySelector('.header .column-headers .column.header.new').textContent).toContain('1')
            this.board.task.children[0].children.push(task())
            await Vue.nextTick().then(() => {
                expect(this.board.$el.querySelector('.header .column-headers .column.header.new').textContent).toContain('2')
            })
        })
        
        it('should only show the unknown column if neccessary', async function() {
            expect(this.board.$el.querySelector('.header .column-headers .column.header.unknown')).toBeNull()
            this.board.task.children[0].children.push(task({ status: 'unknown' }))
            await Vue.nextTick().then(() => {
                expect(this.board.$el.querySelector('.header .column-headers .column.header.unknown').textContent).toContain('unknown 1')
            })
        })
        
        it('shold render one row per task')
        it('should ')
    })
})