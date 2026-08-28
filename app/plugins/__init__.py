"""Die eigenen Quellen der App, als Plugins nach dem Vertrag aus `plugin_api`.

Die App ist ihr eigener erster Plugin-Autor. Das ist keine Übung: Ein Vertrag,
den bisher niemand erfüllt hat, ist eine Behauptung — und die erste Stelle, an
der auffällt, dass eine Rolle unpraktisch geschnitten ist, ist der erste echte
Nutzer.

**Was hier steht, ist Übersetzung und keine zweite Implementierung.** Die
Anbindung an OpenFIGI, Yahoo und justETF gibt es in `app/providers/`; sie wird
von hier benutzt, nicht nachgebaut. Zwei Fassungen derselben Fachregel laufen
beim ersten Sonderfall auseinander, und genau dieser Fall ist hier schon
einmal eingetreten: Ein Ausfall kam als „kenne ich nicht" zurück und wurde
damit zu einem 404.
"""
