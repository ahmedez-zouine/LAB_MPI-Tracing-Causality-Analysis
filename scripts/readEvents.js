/*
 * readEvents.js — Map Thread IDs to MPI Worker Ranks
 */

loadModule("/TraceCompass/Trace")

var trace = getActiveTrace()
var iter = getEventIterator(trace)

// Dictionary: OS thread ID -> MPI worker rank
var tidToWorkerMap = {};

var event = null
while (iter.hasNext()) {
	event = iter.next()

	var eventName = event.getName()

	if (eventName == "ring:init") {
		var tid = getEventFieldValue(event, "context._vtid")
		var worker_id = getEventFieldValue(event, "worker_id")
		tidToWorkerMap[tid] = worker_id
		print("Init -> tid: " + tid + ", worker_id: " + worker_id)

	} else if (eventName == "ring:recv_entry") {
		var tid = getEventFieldValue(event, "context._vtid")
		var worker_id = tidToWorkerMap[tid]
		print("Entering Reception -> tid: " + tid + ", worker_id: " + worker_id)

	} else if (eventName == "ring:recv_exit") {
		var tid = getEventFieldValue(event, "context._vtid")
		var worker_id = tidToWorkerMap[tid]
		var source = getEventFieldValue(event, "source")
		print("Exiting Reception -> tid: " + tid + ", worker_id: " + worker_id + ", source: " + source)

	} else if (eventName == "ring:send_entry") {
		var tid = getEventFieldValue(event, "context._vtid")
		var worker_id = tidToWorkerMap[tid]
		var dest = getEventFieldValue(event, "dest")
		print("Entering Send -> tid: " + tid + ", worker_id: " + worker_id + ", dest: " + dest)

	} else if (eventName == "ring:send_exit") {
		var tid = getEventFieldValue(event, "context._vtid")
		var worker_id = tidToWorkerMap[tid]
		print("Exiting Send -> tid: " + tid + ", worker_id: " + worker_id)
	}
}
