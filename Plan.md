# Gedanken

simplify text-only interaction
  when adding @user or @role switch status to status:doing
  consider a as short as possible status task display. maybe is:doing is better than status:doing?

Wie könnte man den text-storage besser machen?
- locked file interaction from semantic changes Lock, parse, modify, save
- how to do slow / long lastinig text changes without acquiring a long lasting file lock?
    - could use generation, and then show merge view if neccessary? (smells like lots of work)
    - could do crdt based live edting (hard?)

Wei kann man das system zu einem multi-backend single frontend machen? I.e. ich muss mit x bugtrackern / task managern interagieren, habe ein frontend in dem ich alles planen kann und das bestmöglichst status / prioritäten in die einzelnen bug tracker zurück spiegelt?

tree hierarchy navigation plan
  die Anzeige das ein Task kinder hat ist in der metadata bar der subtasks
  das ist momentan etwas komisch, weil alle anderen elemente dort buttons sind
  man aber auf die dazugehörige story muss (also eine level höher) um ein level nach unten zu navigieren und die kind-elemente zu sehen.
  evtl. also doch auch von hier einen level abstieg ermöglichen?

command pattern um die änderungen semantisch als aktionsliste abzuspeichern und auszutauschen
* undo queue dadurch gut ausdrückbar
  * undo erst mal nur für meine änderunen, änderungen von anderen leuten zurücknehmen ist ein unabhängiges kommando
* text-änderungen anhand von semantischem verständnis in undo aktionen einteilen
  * das könnte ein gutes interface zu den operational transforms sein, die in ihrer natur viel feinkörniger sind

Wie müsste denn eine Vuejs implementierung von dem Task Tracker aussehen?

* Syntax sollte wo möglich an markdown angelehnt sein, damit die lernkurve kleiner ist
* TextEditor der halbwegs vernünftig bedienbar ist - markdown support wäre schön
* switch für preview, eventuell auch side-by-side oder top-bottom
* papierkorb für alle tickets die man aus dem text gelöscht hat, damit sie nicht einfach verloren gehen
  * explizites löschen von hier
* ids werden automatisch angefügt wenn das ticket erstellt ist und sind klickbar? (neues fenster, damit man keinen state verliert)
* Idealerweise integriert sich das dashboard mittels adaptoren mit ticket systemen. I.e. wir könnten Track weiter verwenden, bzw. das ticket-system wechseln.
  * Notwendig wäre nur:
    * ID und Titel lesen und schreiben
    * hierarchien von tickets auslesen und schreiben
* Nach bedarf können weitere meta-informationen zu der text-darstellung hinzugefügt werden
  * Assignments: @mh @rb?
  * Status (keine Ahnung was die richtige syntax ist)
  * Ticket Art: Task, Story, Bug, …

* darstellung von tickets die es erlaubt mehr informationen einzublenden

      - nur titel #23
      + titel und #24
              content beschreibung so dass man prose nutzen kann
              wenn man das + durch ein - ersetzt wird der content ausgeblendet

              idealerweise auch wenn man draufklickt?

          - subticket?

* Use TODO.TXT syntax where possible.
  * https://github.com/samuelsnyder/outline-todo.txt for ideas about inheritance of info so you don't have to rewrite everything on child lines
    * id:1234 for ticket ids
  * use tag:value syntax for metadata

* Super-Bonus: ein Text-format das aus markdown eine todotxt sektion extrahiert
    ```todotxt
    task 1
    task 2
      subtask 1
      subtask 2
    ```
    
    quasi als markdown processor? Schick wenn man das in andere markdown editoren einbinden könnte
      Evaluieren ob man dadurch schön eine beschreibung eines features (minimal marketable oder sowas?) haben kann und dann danach die konkreten tasks und subtasks um das zu implementieren
      Unklar ob das so wertvoll ist, wenn man eigentlich mit bug trackern arbeiten will
    Damit könnte man ein formatiertes dokument haben, das auch die todo-liste des projektes enthällt
    Um das zu skalieren müsste man vermutlich alle sub tasks ab einer bestimmten ebene in einem anderen file (datenbank?) ablegen
    Extra bonus wenn man so eine Projekt-Dokuemntation verwalten / extrahieren kann - stichwort change-notes

Consider making it easier to work with a flat file in git
  auto-commit todo.txt changes
    regularly
    or after changes?
    Not sure what that gives you if you don't auto-push and pull as well, as others will not see the change
      But auto push/pull seems _really_ nasty, as it totally messes with your repo otherwise
      Could work if it's it's own repo though
      Would also need to alert user on any changes outside of the todotxt that the app didn't trigger
      so he can fix the conflict/ solve the problem

https://github.com/AnthonyDiGirolamo/todotxt-machine/blob/master/todotxt_machine/todo.py
https://github.com/samuelsnyder/outline-todo.txt
https://github.com/todotxt/todo.txt-cli/wiki/Tips-and-Tricks
https://github.com/todotxt/todo.txt-cli/wiki/How-To's
https://github.com/todotxt/todo.txt

Consider using modern js and css standards
* import and modules to structure js code
* js template literals to have the html templates together with the js
* in browser sass compilation for the sass https://github.com/Neos21/in-browser-sass

https://github.com/FirebaseExtended/firepad

https://github.com/ipfs/research-CRDT

https://xotlcrdt.readthedocs.io/en/latest/

research https://rollupjs.org/guide/en to build bundle?

# Wie könnte das Sync-Protokoll aussehen?

Inspiriert durch CRDTs? Evtl. ist die Datenbasis ganz konkret ein CRDT und wird schlicht nur mit einer Kopie auf dem Server synced? Das hätte den Vorteil das auf client-seite einfach direkt gegen den CRDT die UI läuft. Ob State-Based sync oder operations based sync macht dann nur einen unterschied wie die events angebunden sind.

Es gibt massig große crdt basierte datenbanken die den ganzen sync übernehmen - einige auch open source. @see https://github.com/topics/crdt

Vielleicht reicht es aber auch erst mal ganz einfach anzufangen? Also: Dom Events sind operations, und diese Operation objekte werden an den Server geschickt. Dieser sendet (via socket.io?) auch operation objekte zurück - und wenn diese den state nicht verändern, dann verändern sie ihn eben nicht. Primitiv, aber ganz gut um mit diesem Programmiermodell Erfahrung zu sammeln. Späteres Umstellen auf CRDTs ist vermutlich möglich.

Wenn ich ein CRDT basiertes Modell haben will - so wie jetzt das json nested ist, muss ich spätestens dann eine Art und Weise haben die einzelnen Tasks zu addressieren. Das geht über einen Pfad (mit problemen) oder über die ID (klingt einfacher). Sowohl Server als auch Client müssen dann in der Lage sein solche 'Operations' anzuwenden.

Ziel: socket.io connection zu asynchronem server, darüber id/uuid basierte messages die mutationen ausführen.
- id:quoox set_tag: status:closed
- id:foo add_child id:bar line:'hello there what a nice task'
- id:baz
- id:baz remove
- id:foo move_child id:bar offset:10 # later

Consider sending out the normalized json to all clients to normalize the state.

Consider the use of montonous, vector and matrix clocks
- client can have a data_generation: Int property that gets sent to the server with each change. Thus the server can easily check that the client is on the current data generation and eventually send the client a undo / error message to correct the problem.
- Client could have a vector clock with a data_generation for each task, so changes to each task individually can be conflict detected.
- server could use a matrix clock to track the current best known state of each client

A simple monotonous clock on the client could allow the server to handle all serializing. That would allow to just send the full json to the client again as there is no trigger cycle.
