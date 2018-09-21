import importSCSS from './utils.js'
importSCSS('/static/whiteboard.sass')

// REFACT consider to allow only viewing either the text or the gui interface - tabbed style?

function generateClientUniqueID() {
  if (undefined === generateClientUniqueID.cuid) {
    generateClientUniqueID.cuid = 0;
  }
  return generateClientUniqueID.cuid++;
}

export default {
    template: `
    <div class=whiteboard v-bind:title="task.line">
    
      <div class=header>
        <nav aria-label=breadcrumb>
          <ol class=breadcrumb>
            <li class="breadcrumb-item"
              v-for="crumb in breadcrumbs"
              v-on:click.prevent.stop="browse(crumb)"
              v-bind:key="crumb.id || generateClientUniqueID()"
            >
              <!-- FIXME href should point to actual ticket in tracker -->
              <a href=#><span class=id v-if=crumb.id>#{{ crumb.id }}</span>{{ crumb.line || 'root' }}</a>
            </li>
          </ol>
        </nav>
        <h1 v-if="(task.line || '').length"><a v-if="task.id" href="#" class="id" v-text="'#' + task.id"></a>{{ task.line }}</h1>
        <div class="column-headers">
          <h2 class="column header" 
            v-for="columnName in ['new', 'unknown', 'doing', 'done']"
            v-if="columnName !== 'unknown' || countOfGrandChildrenInStatus(task, 'unknown') > 0" 
            v-bind:class="[columnName]"
            v-bind:style="{ width: Math.floor(100 / numberOfColumns) + '%' }"
            v-bind:key="columnName"
          >{{ columnName }} <span class="grandchild-count" >{{ countOfGrandChildrenInStatus(task, columnName) }}</span></h2>
        </div>
      </div>
      
      <div class="task"
        v-for="child in task.children"
        v-bind:title="child.line"
        v-bind:class="{ is_done: child.is_done }"
        v-bind:key="child.id || generateClientUniqueID()"
      >
        <div class="container-fluid">
          <div class="row">
            <div class="col status" 
              v-for="columnName in ['new', 'unknown', 'doing', 'done']"
              v-if="columnName !== 'unknown' || countOfGrandChildrenInStatus(task, 'unknown') > 0" 
              v-bind:class="[columnName]"
              v-bind:key="columnName"
            >
              <h2 class=metadata 
                v-if="columnName === 'new'"
                v-on:click.prevent="toggleCollapsed($event, child)"
              >
                <!-- FIXME herf should point to bugtracker url -->
                <a href="#" class="id" v-text="'#' + child.id"></a>
                <span class="title" v-text="child.line"></span>
                <a v-on:click.prevent.stop="browse(child)" href="#" class="browse button" title="Browse grandchildren Tasks">⏎</a>
                <a v-on:click.prevent.stop="addChildTask(child)" href="#" class="add button" title="Add subtask">+</a>
              </h2>

              <h2 class=metadata  v-if="columnName === 'done'">
                <span class=flexspace></span>
                <span class="stats" v-text="childrenInStatus(child, 'done').length + '/' + child.children.length"></span>
              </h2>
              
              <draggable class="drag-container"
                v-model="childrenInStatus(child, columnName)"
                v-bind:options="{ group: String(cuid(child)), sort: false }"
                v-on:end="onDragEnd"
                v-bind:data-status="columnName"
              >
                <!-- REFACT use v-key to allow animations between orderings and column change (not sure this is possible) -->
                <div class="col subtask" 
                  v-for="grandChild in childrenInStatus(child, columnName)" 
                  v-bind:title="grandChild.line"
                  v-bind:key="grandChild.id || generateClientUniqueID()"
              >
                  <h3>
                    <span class="metadata">
                        <a href="#" class="edit button" title="Edit this task">✎</a>
                        <span class="child-indicator" title="Has child tasks" v-if="grandChild.children.length > 0"></span>
                        <a href="#" class="id" v-text="'#' + grandChild.id" title="External Link to task"></a>
                    </span>
                    <span class="title" v-text="grandChild.line"></span>
                    <span class="contexts" v-text="grandChild.contexts.join(', ')"></span>
                  </h3>
                </div>
              </draggable>
              
            </div>
          </div>
        </div>
      </div>
      
    </div>`,
  props: {
    rootTask: {
      type: Object,
      required: true
    }
  },
  data: function() {
    return {
      task: this.rootTask,
      breadcrumbs: [this.rootTask]
    };
  },
  // watch: {
  //   task: {
  //     handler: function(val) {
  //       // TODO replace with fetch()
  //       $.ajax({
  //         url: "/api/v1/todos",
  //         type: "POST",
  //         data: JSON.stringify(val),
  //         contentType: "application/json"
  //       }).then(response => (this.data = response.json));
  //     },
  //     deep: true
  //   }
  // },
  computed: {
    numberOfColumns: function() {
      if (this.countOfGrandChildrenInStatus(this.task, "unknown") > 0) {
        return 4;
      } else {
        return 3;
      }
    }
  },

  methods: {
    
    generateClientUniqueID: generateClientUniqueID,

    subtaskCount: function(task) {
      return task.children.length
    },
    
    childrenInStatus: function(task, status) {
      return task.children.filter(child => status === child.status)
    },
    
    countOfGrandChildrenInStatus: function(task, status) {
      return (task.children || [])
        .map(child => this.childrenInStatus(child, status).length)
        .reduce((accumulator, each) => accumulator + each, 0);
    },

    addChildTask: function(task) {
      // TODO add UI to enter text
      // REFACT consider to require using the text interface to do this
      task.children.new.push({
        line: "",
        id: "",
        status: 'new',
        is_done: false,
        projects: [],
        contexts: [],
        tags: {},
        children: [],
      });
    },

    toggleCollapsed: function($event) {
      var $task = $($event.currentTarget).closest(".task");
      $task.toggleClass("toggle-collapsed");
    },
    
    onDragEnd: function(event) {
      // whats the right way to get at the vue element? __vue__ seems fishy
      const draggedTask = event.from.__vue__.context.element
      draggedTask.status = event.to.dataset.status
    },
    
    browse: function(task) {
      const index = this.breadcrumbs.indexOf(task);
      if (-1 === index) {
        this.breadcrumbs.push(task);
      } else {
        // don't remove the clicked element, as it's needs to remain tip of the stack
        this.breadcrumbs.splice(index + 1);
      }
      this.task = task;
    },
    
    // REFACT this should be a server side given ID in almost all cases
    // i.e. I need a concept to get rid of these asap, even if they are needed as stopgaps
    cuid: function(task) {
      if (undefined === task.cuid) {
        task.cuid = generateClientUniqueID();
      }
      return task.cuid;
    }
  }
};