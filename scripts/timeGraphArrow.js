loadModule("/TraceCompass/Trace")
loadModule("/TraceCompass/Analysis")
loadModule("/TraceCompass/DataProvider")
loadModule("/TraceCompass/View")
loadModule('/TraceCompass/Utils');

var trace = getActiveTrace()

var iter = getEventIterator(trace)
var tidToWorkerMap = {};

var analysis = createScriptedAnalysis(trace, "ringTimeLine.js")
var ss = analysis.getStateSystem(false);

var pendingArrows = {};
var arrows = [];

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
		
		pending = pendingArrows[worker_id];
		if (pending != null) {
			pendingArrows[worker_id] = null;
			pending["endTime"] = event.getTimestamp().toNanos();
			arrows.push(pending);
		}
	} else if (eventName == "ring:send_entry") {
		tid = getEventFieldValue(event, "context._vtid")
		worker_id = tidToWorkerMap[tid]
		dest = getEventFieldValue(event, "dest")
		quark = ss.getQuarkAbsoluteAndAdd(worker_id);
		ss.modifyAttribute(event.getTimestamp().toNanos(), "Sending", quark);

		pendingArrows[dest] = {"time" : event.getTimestamp().toNanos(), "source" : worker_id, "dest" : dest};
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

var tgEntries = createListWrapper();
var tgArrows = createListWrapper();

var mpiWorkerToId = {};

var workerIds = [];
for (var tid in tidToWorkerMap) {
	var wid = "" + tidToWorkerMap[tid];
	var alreadyIn = false;
	for (var k = 0; k < workerIds.length; k++) {
		if (workerIds[k] === wid) { alreadyIn = true; break; }
	}
	if (!alreadyIn) { workerIds.push(wid); }
}

var mpiEntries = [];
for (var i = 0; i < workerIds.length; i++) {
	var wid = workerIds[i];
	var quark = ss.getQuarkAbsoluteAndAdd(wid);
	var entry = createEntry(wid, {'quark' : quark});
	mpiWorkerToId[wid] = entry.getId();
	mpiEntries.push(entry);
}

mpiEntries.sort(function(a,b){return Number(a.getName()) - Number(b.getName())});
for (var i = 0; i < mpiEntries.length; i++) {
	tgEntries.getList().add(mpiEntries[i]);
}

for (var i = 0; i < arrows.length; i++) {
	var arrow = arrows[i];
	var srcId = mpiWorkerToId[String(arrow["source"])];
	var dstId = mpiWorkerToId[String(arrow["dest"])];
	var startTime = arrow["time"];
	var duration = arrow["endTime"] - startTime;
	if (srcId != null && dstId != null) {
		tgArrows.getList().add(createArrow(srcId, dstId, startTime, duration, 1));
	}
}

var entriesList = tgEntries.getList();
var arrowsList  = tgArrows.getList();

var getEntriesFunction = new JavaAdapter(java.util.function.Function, {
	apply: function(parameters) {
		return entriesList;
	}
});

var getArrowsFunction = new JavaAdapter(java.util.function.Function, {
	apply: function(parameters) {
		return arrowsList;
	}
});

provider = createScriptedTimeGraphProvider(analysis, getEntriesFunction, null, getArrowsFunction);
if (provider != null) {
	openTimeGraphView(provider);
}
