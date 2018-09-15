<template>
<div class=whiteboard v-bind:title="task.line">
    <div class=header>
      <nav aria-label=breadcrumb>
        <ol class=breadcrumb>
          <li class="breadcrumb-item"
            v-for="crumb in [task].concat(breadcrumbs)"
            v-on:click.prevent.stop="browse(crumb)"
            v-bind:key="crumb.id || generateClientUniqueID()"
          >
            <!-- FIXME href should point to actual ticket in tracker -->
            <a href=#><span class=id v-if=crumb.id>#{{ crumb.id}}</span>{{ crumb.line || 'root' }}</a>
          </li>
        </ol>
      </nav>
      <h1 v-if="task.line.length"><a v-if="task.id" href="#" class="id" v-text="'#' + task.id"></a>{{ task.line }}</h1>
      <div class="column-headers">
        <h2 class="column header" 
          v-for="columnName in ['new', 'unknown', 'doing', 'done']"
          v-if="columnName !== 'unknown' || countOfGrandChildrenInStatus(task, 'unknown') > 0" 
          v-bind:class="[columnName]"
          v-bind:style="{ width: Math.floor(100 / numberOfColumns) + '%' }"
          v-bind:key="columnName"
        >{{ columnName }} <span class="grandchild-count" v-text="countOfGrandChildrenInStatus(task, columnName)"></span></h2>
      </div>
    </div>
    <div class="task"
      v-for="child in children(task)"
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
              <span class="stats" v-text="child.children.done.length + '/' + subtaskCount(child)"></span>
            </h2>
            <draggable class="drag-container"
              v-model="child.children[columnName]"
              v-bind:options="{group:String(cuid(child))}"
            >
              <!-- REFACT use v-key to allow animations between orderings and column change (not sure this is possible) -->
              <div class="col subtask" 
                v-for="grandChild in child.children[columnName]" 
                v-bind:title="grandChild.line"
                v-bind:key="grandChild.id || generateClientUniqueID()"
            >
                <h3>
                  <span class="metadata">
                      <a href="#" class="edit button" title="Edit this task">✎</a>
                      <span class="child-indicator" title="Has child tasks" v-if="children(grandChild).length > 0"></span>
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
  </div>
</template>

<script>
import $ from 'jquery'

// REFACT consider to allow only viewing either the text or the gui interface - tabbed style?

function generateClientUniqueID() {
    if (undefined === generateClientUniqueID.cuid) {
        generateClientUniqueID.cuid = 0
    }
    return generateClientUniqueID.cuid++;
}

export default {
    props: {
        rootTask: {
            type: Object,
            required: true,
        },
    },
    data: function() {
        return {
            task: this.rootTask,
            breadcrumbs: [this.rootTask],
        }
    },
    watch: {
        task: {
            handler: function(val) {
                $.ajax({
                    url: '/api/v1/todos', type: 'POST', 
                    data: JSON.stringify(val), 
                    contentType: 'application/json'
                }).then(response => this.data = response.json)
            },
            deep: true,
        },
    },
    computed: {
        
        numberOfColumns: function() {
            if (this.countOfGrandChildrenInStatus(this.task, 'unknown') > 0) {
                return 4
            }
            else {
                return 3
            }
        },
    },
    
    methods: {
        generateClientUniqueID: generateClientUniqueID,
        
        subtaskCount: function(task) {
            return task.children.new.length
                + task.children.unknown.length
                + task.children.doing.length
                + task.children.done.length;
            },
            children: function(task) {
            const children = []
            children.push.apply(children, task.children.new)
            children.push.apply(children, task.children.unknown)
            children.push.apply(children, task.children.doing)
            children.push.apply(children, task.children.done)
            return children
        },
        
        countOfGrandChildrenInStatus: function(task, status) {
            return this.children(task)
                .map( (each) => each.children[status].length )
                .reduce( (accumulator, each) => accumulator + each, 0)
        },
        
        addChildTask: function(task) {
            // TODO add UI to enter text
            // REFACT consider to require using the text interface to do this
            task.children.new.push({
                line: '',
                id: '',
                is_done: false,
                projects: [],
                contexts: [],
                tags: {},
                children: { new: [], unknown: [], doing: [], done: []},
            })
        },
        
        toggleCollapsed: function($event) {
            var $task = $($event.currentTarget).closest('.task')
            $task.toggleClass('toggle-collapsed')
        },
        
        browse: function(task) {
            const index = this.breadcrumbs.indexOf(task)
            if (-1 === index) {
                this.breadcrumbs.push(task)
            }
            else {
                // don't remove the clicked element, as it's needs to remain tip of the stack
                this.breadcrumbs.splice(index + 1)
            }
            this.task = task
        },
        
        cuid: function(task) {
            if (undefined === task.cuid) {
                task.cuid = generateClientUniqueID()
            }
            return task.cuid;
        },
    },
}
</script>

<style lang="scss" scoped>

$dark_grey: rgb(102, 102, 102);
$light_grey: rgb(153, 153, 153);

$button_color: #6E94B8;
$accent_background_color: #F2F2F2;

.whiteboard {
  width: 100%;
  height: 50%;
  padding-top: 10px;
  
  .breadcrumb {
    background-color: $accent_background_color;
  }
  
  .header h1 {
    font-size: 24px;
    text-align: center;
  }
  
  .header h2.column {
    font-size: 12px;
    color: $dark_grey;
    display: inline-block;
    text-align: center;
  }
  
  .grandchild-count {
    background-color: $light_grey;
    color: white; // REFACT $inverse_text_color?
    padding: 0 8px;
    border-radius: 8px;
  }

  .task {
    width: 100%;
    position: relative;
    
    &.toggle-collapsed, &.is_done {
      height: 20px;
      overflow: hidden;
    }
    
    &.is_done.toggle-collapsed {
      height: 100%;
      overflow: default;
    }
    
    .col > .metadata {
      cursor: ns-resize;
    }
    
    .status.new {
      position: relative;
    }
    
    .metadata {
      position: absolute;
      z-index: 100;
      font-size: 12px;
      line-height: 18px;
      height: 18px;
      text-shadow: white 0px 1px 0px;
    
      top: 0;
      left: 0;
      right: 0;
      text-overflow: ellipsis;
      white-space: nowrap;
      overflow: hidden;
      
      display: flex;
      
      .flexspace {
        flex: auto;
      }
      
      .title {
        // display: none
        flex: 1;
        overflow: hidden;
        text-overflow: none;
        text-overflow: '-';
      }
      
      /* TODO switch to non absolute layout for the metadata bar and pull out unifications */
      .id {
        font-size: 10px;
        color: $dark_grey; // fix link color
        padding: 0px 2px;
      }
      
      .stats {
        color: $light_grey;
        margin-right: 10px;
      }
      
      .button {
        height: 14px;
        line-height: 10px;
        float: right;
        padding: 2px 3px;
        font-size: 12px;
        color: $button_color;
        box-shadow: inset 0px 0px 4px white;
        border: 1px solid transparent;
      }
      
      .button:hover {
        border: 1px solid #CDCDCD;
        box-shadow: inset 0px 0px 4px rgba($light_grey, .11);
      }
      
      .child-indicator::before {
        content: '…';
        width: 14px;
        height: 14px;
        line-height: 10px;
        position: absolute;
        top: 1px;
        right: 18px;
        padding: 2px 3px;
        font-size: 12px;
        color:  $button_color;
      }
      
    }
    
    .status {
      min-height: 100px;
      border: 1px solid $light_grey;
      border-left: none;
      border-bottom: none;
      padding-top: 18px;
      padding-left: 2px;
      padding-right: 2px;
      
      &.new, &.done {
       background-color: $accent_background_color;
      }
      
      &.doing {
        background-color: white;
      }
      
      &.done .metadata {
        justify-content: end;
      }
      
    }
    
    .drag-container {
      width: 100%;
      min-height: 80px;
    }
    
    .subtask {
      display: inline-block;
      float: left;
      margin: 2px;
      height: 80px;
      width: 104px;
      cursor: move;
      border: 1px solid rgb(204, 204, 204);
      background-color: white;
      box-shadow: $light_grey 0px 1px 2px 0px;
      font-size: 12px;
      position: relative;
    
      padding-top: 20px;
      padding-left: 5px;
      padding-right: 5px;
      padding-bottom: 15px;
    
      overflow: hidden;
      
      .metadata {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 18px;
        font-size: 10px;
        line-height: 18px;
        display: inline-block;
        width: 100%;
        background-color: $accent_background_color;
        
        .id {
          color: $dark_grey;
        }
        
      }
      
      > * {
        font-size: 12px;
        height: 36px;
        line-height: 18px;
        text-overflow: ellipsis;
        overflow: hidden;
      }
      
      .contexts {
        color: $dark_grey;
        position: absolute;
        left: 5px;
        right: 5px;
        bottom: 5px;
        white-space:nowrap;
        text-overflow:ellipsis;
        overflow:hidden;
        font-size: 10px;
        line-height: 18px;
      }
      
    }
    
  }
}



</style>