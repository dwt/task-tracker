# Relativ konkrete Todos

* Tasks bearbeiten mittels content editable auf doppelklick?
  * evtl. auch via status change und enter als commit?
  * in jedem fall sollte der edit bereich entweder größer oder auto resizing sein, damit man komfortabel tippen kann

* Vue app aus dem index html irgendwie herausholen, damit highlighting etc. im editor funktioniert
  * Wenn möglich ohne gleich eine shitload an JS dependencies und extra prozesse dazu zu kriegen

* Async Flask app und sync mit dem server on browser changes
  * socket.io? was benutzt man da am besten für websockets?

# Gedanken

Wie müsste denn eine Vuejs implementierung von dem Task Tracker aussehen?

* Syntax sollte wo möglich an markdown angelehnt sein, damit die lernkurve kleiner ist
* TextEditor der halbwegs vernünftig bedienbar ist - markdown support wäre schön
* switch für preview, eventuell auch side-by-side oder top-bottom
* papierkorb für alle tickets die man aus dem text gelöscht hat, damit sie nicht einfach verloren gehen
  * explizites löschen von hier
* ascii format für tickets. Some thoughts

      - We want to foo the bar #23
        - Bar the bars #24
        - Foo the foos #25

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


https://github.com/AnthonyDiGirolamo/todotxt-machine/blob/master/todotxt_machine/todo.py
https://github.com/samuelsnyder/outline-todo.txt
https://github.com/todotxt/todo.txt-cli/wiki/Tips-and-Tricks
https://github.com/todotxt/todo.txt-cli/wiki/How-To's
https://github.com/todotxt/todo.txt
