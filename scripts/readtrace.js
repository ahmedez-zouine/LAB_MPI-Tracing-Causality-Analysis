loadModule("/TraceCompass/Trace")

var trace = getActiveTrace()

var iter = getEventIterator(trace)
var event = null
while (iter.hasNext()) {
	event = iter.next()

	eventString = event.getName() + " --> ( "

	var fieldsIterator = event.getContent().getFieldNames().iterator()
	while (fieldsIterator.hasNext()) {
		eventString += fieldsIterator.next() + " "
	}
	eventString += ")"

	print(eventString);
}