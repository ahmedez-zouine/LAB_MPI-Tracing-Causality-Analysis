

loadModule("/TraceCompass/Trace")
loadModule("/TraceCompass/Analysis")

var trace = getActiveTrace()
var iter = getEventIterator(trace)

// Dictionary: OS thread ID -> MPI worker rank
var tidToWorkerMap = {};

var analysis = createScriptedAnalysis(trace, "ringTimeLine.js")
var ss = analysis.getStateSystem(false);

var event = null
while (iter.hasNext()) {
	event = iter.next()

	var eventName = event.getName()

	if (eventName == "ring:init") {
		var tid = getEventFieldValue(event, "context._vtid")
		var worker_id = getEventFieldValue(event, "worker_id")
		tidToWorkerMap[tid] = worker_id

	} else if (eventName == "ring:recv_entry") {
		var tid = getEventFieldValue(event, "context._vtid")
		var worker_id = tidToWorkerMap[tid]
		var quark = ss.getQuarkAbsoluteAndAdd(worker_id);
		ss.modifyAttribute(event.getTimestamp().toNanos(), "Waiting for reception", quark);

	} else if (eventName == "ring:recv_exit") {
		var tid = getEventFieldValue(event, "context._vtid")
		var worker_id = tidToWorkerMap[tid]
		var quark = ss.getQuarkAbsoluteAndAdd(worker_id);
		ss.removeAttribute(event.getTimestamp().toNanos(), quark);

	} else if (eventName == "ring:send_entry") {
		var tid = getEventFieldValue(event, "context._vtid")
		var worker_id = tidToWorkerMap[tid]
		var quark = ss.getQuarkAbsoluteAndAdd(worker_id);
		ss.modifyAttribute(event.getTimestamp().toNanos(), "Sending", quark);

	} else if (eventName == "ring:send_exit") {
		var tid = getEventFieldValue(event, "context._vtid")
		var worker_id = tidToWorkerMap[tid]
		var quark = ss.getQuarkAbsoluteAndAdd(worker_id);
		ss.removeAttribute(event.getTimestamp().toNanos(), quark);
	}
}

if (event != null) {
	ss.closeHistory(event.getTimestamp().toNanos());
}
