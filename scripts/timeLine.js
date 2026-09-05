loadModule("/TraceCompass/Trace")
loadModule("/TraceCompass/Analysis")
loadModule("/TraceCompass/DataProvider")
loadModule("/TraceCompass/View")

var trace = getActiveTrace()

var iter = getEventIterator(trace)
var tidToWorkerMap = {};

var analysis = createScriptedAnalysis(trace, "ringTimeLine.js")
var ss = analysis.getStateSystem(false);

var event = null
while (iter.hasNext()) {
	event = iter.next()

	eventName = event.getName()
	if (eventName == "ring:init") {
		tid = getEventFieldValue(event, "context._vtid")
		worker_id = getEventFieldValue(event, "worker_id")
		tidToWorkerMap[tid] = worker_id
	} else if (eventName == "ring:recv_entry") {
		tid = getEventFieldValue(event, "context._vtid")
		worker_id = tidToWorkerMap[tid]
		quark = ss.getQuarkAbsoluteAndAdd(worker_id);
		ss.modifyAttribute(event.getTimestamp().toNanos(), "Waiting for reception", quark);
	} else if (eventName == "ring:recv_exit") {
		tid = getEventFieldValue(event, "context._vtid")
		worker_id = tidToWorkerMap[tid]
		source = getEventFieldValue(event, "source")
		quark = ss.getQuarkAbsoluteAndAdd(worker_id);
		ss.removeAttribute(event.getTimestamp().toNanos(), quark);
	} else if (eventName == "ring:send_entry") {
		tid = getEventFieldValue(event, "context._vtid")
		worker_id = tidToWorkerMap[tid]
		dest = getEventFieldValue(event, "dest")
		quark = ss.getQuarkAbsoluteAndAdd(worker_id);
		ss.modifyAttribute(event.getTimestamp().toNanos(), "Sending", quark);
	} else if (eventName == "ring:send_exit") {
		tid = getEventFieldValue(event, "context._vtid")
		worker_id = tidToWorkerMap[tid]
		quark = ss.getQuarkAbsoluteAndAdd(worker_id);
		ss.removeAttribute(event.getTimestamp().toNanos(), quark);
	}
}

if (event != null) {
	ss.closeHistory(event.getTimestamp().toNanos());
}

// Create the Time Graph Data Provider and open the view!
var map = new java.util.HashMap();
map.put(ENTRY_PATH, '*');
provider = createTimeGraphProvider(analysis, map);
if (provider != null) {
	openTimeGraphView(provider);
}
