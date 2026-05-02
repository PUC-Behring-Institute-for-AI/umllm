const UM = (() => {

    function init() {
        $("#clear").on("click", onClear);
        $("#prev").on("click", onPrev);
        $("#next").on("click", onNext);
        $("#cycle").on("click", onCycle);
        $("#reset").on("click", onReset);
        refresh();
    }

    function onClear() {
        $.postJSON("/api/clear", {},
                   (response) => {refresh(response)},
                   (xhr) => console.error("Error:", xhr.responseText));
    }

    function onPrev() {
        $.postJSON("/api/prev", {},
                   (response) => {refresh(response)},
                   (xhr) => console.error("Error:", xhr.responseText));
    }

    function onNext() {
        $.postJSON("/api/next", {},
                   (response) => {refresh(response)},
                   (xhr) => console.error("Error:", xhr.responseText));
    }

    function onCycle() {
        $.postJSON("/api/cycle", {},
                   (response) => {refresh(response)},
                   (xhr) => console.error("Error:", xhr.responseText));
    }

    function onReset() {
        $.postJSON("/api/reset", {},
                   (response) => {refresh(response)},
                   (xhr) => console.error("Error:", xhr.responseText));
    }

    function refresh(response) {
        if (response) {
            filename = response.filename;
            um = response.um;
        }
        if (filename) {
            $("#filename").text("UMLLM: " + filename)
        } else {
            $("#filename").text("UMLLM")
            $("#prev, #next, #cycle, #reset").prop("disabled", true);
        }
        $("#machine").html(um.formatted_machine || "");
        $("#halt").html(um.halt || "");
        $("#work").html(um.formatted_work || "");
        $("#state").html(um.state || "");
        $("#symbol").html(um.symbol || "");
        $("#left_symbol").html(um.left_symbol || "");
        $("#next_state").html(um.next_state || "");
        $("#next_symbol").html(um.next_symbol || "");
        $("#next_move").html(um.next_move || "");
        $("#subst1").html(um.subst1 || "");
        $("#subst2").html(um.subst2 || "");
        $("#steps").html(um.steps || "");
        if ("prev_step" in um && um.prev_step) {
            $("#prev, #reset").prop("disabled", false);
            $("#prev").text("Prev (" + um.prev_step + ")");
        } else {
            $("#prev, #reset").prop("disabled", true);
            $("#prev").text("Prev");
        }
        if ("next_step" in um && um.next_step) {
            $("#next, #cycle").prop("disabled", false);
            $("#next").text("Next (" + um.next_step + ")");
        } else {
            $("#next, #cycle").prop("disabled", true);
            $("#next").text("Next");
        }
    }

    // AJAX helper
    $.postJSON = function (url, data, success, error) {
        $.ajax({
            url,
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(data),
            success,
            error: error || ((xhr) =>
                console.error("Error:", xhr.responseText)),
        });
    };

    return {init};
})();

$(document).ready(UM.init);
