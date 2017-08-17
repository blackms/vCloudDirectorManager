/**
 * Created by alessio.rocchi on 15/07/2015.
 */

function reloadData() {
    console.log("Reloading data...");
    $.ajax({
        type: "GET",
        url: "/trigger_run",
        timeout: 10000,
        success: function () {
            alert('Data reloading triggered...');
        },
        error: function (xhRequest, ErrorText, thrownError) {
            alert('Failed to trigger reloading, check console.');
            console.log(xhRequest, ErrorText, thrownError);
        }
    })
}

function vdcClick(param) {
    console.log($(param));
    var vdcId = $(param).closest('tr').attr('id');
    var dialogMessage = $("#dialog-message");
    var actualGhzAllocated = $("#" + vdcId + "_ghz").text();
    var actualRamAllocated = $("#" + vdcId + "_ram").text();
    /* Initializing form value */
    $("#allocatedGhz").val(actualGhzAllocated);
    $("#allocatedRam").val(actualRamAllocated);
    dialogMessage.dialog({
        modal: true,
        title: vdcId,
        width: 600,
        height: 425,
        buttons: {
            Close: function () {
                $(this).dialog("close");
            },
            Apply: function () {
                var Data = {
                    'ghzAmount': $("#allocatedGhz").val(),
                    'ramAmount': $("#allocatedRam").val(),
                    'vdcId': vdcId
                };
                console.log(Data);
                $.ajax({
                    type: "POST",
                    url: "/update_vdc",
                    timeout: 240000,
                    data: Data,
                    success: function () {
                        var element = $("#setNotification");
                        element.addClass("alert-success");
                        element.html("VDC Updated successfully.");
                    },
                    error: function () {
                        var element = $("#setNotification");
                        element.addClass("alert-danger");
                        element.html("Failed to update VDC!");
                    }
                });
            }
        }
    });
}

function storageClick(param) {
    var vdcId = $(param).closest('tr').attr('id');
    console.log(vdcId);
    var dialogMessage = $("#storage-dialog-message");
    var storageName = $(param).data('name');
    console.log(storageName);
    var actualSpace = $(param).text();
    console.log(actualSpace);
    $("#allocatedStorage").val(actualSpace);
    dialogMessage.dialog({
        modal: true,
        title: vdcId + ': ' + storageName,
        width: 600,
        height: 425,
        buttons: {
            Close: function () {
                $(this).dialog("close");
            },
            Apply: function () {
                var Data = {
                    'storageName': storageName,
                    'gbAmount': $("#allocatedStorage").val(),
                    'vdcId': vdcId
                };
                console.log(Data);
                $.ajax({
                    type: "POST",
                    url: "/update_storage",
                    timeout: 240000,
                    data: Data,
                    success: function () {
                        var element = $("#storageSetNotification");
                        element.addClass("alert-success");
                        element.html("Storage Profile Updated successfully.");
                    },
                    error: function () {
                        var element = $("#storageSetNotification");
                        element.addClass("alert-danger");
                        element.html("Failed to update Storage Profile!");
                    }
                });
            }
        }
    });
}

function actionEditMetadata(param) {
    var orgName = $(param).attr('value');
    console.log(orgName);
    var dialogMessage = $("#editMetadata-dialog-message");
    // Start to populate form with the correct values
    var MetaData = ["OrderNumber", "CustomerPhone", "CustomerEmail", "LicSqlStdAmount", "LicSqlEntAmount", "LicWinAmount", "ExpirationData"];
    $("#formEditMetadata").html('');
    $.each(MetaData, function (index, value) {
        var realValue = $("#"+ orgName + value).attr('value');
        console.log(realValue);
        $('#formEditMetadata').append('<div>' +
            '<label for="' + value + '">' + value + '</label>' +
            '<input name="' + value + '" id="' + value + '" class="form-control" type="text" value="' + realValue + '">' +
            '</div>')
    });
    var expirationData = $('input[id=ExpirationData]');
    expirationData.datepicker({
        format: "dd/mm/yy",
        weekStart: 1
    });

    dialogMessage.dialog({
        modal: true,
        title: "Edit MetaData for " + orgName,
        width: 600,
        height: 600,
        buttons: {
            Close: function () {
                if (expirationData.val() == 'undefined') {
                    var element = $("#editMetaDataNotification");
                    element.removeClass("alert-success").addClass("alert-danger");
                    element.html("ExpirationData cannot be undefined.");
                    return;
                }
                $(this).dialog("close");
            },
            Edit: function () {
                if (expirationData.val() == 'undefined') {
                    var element = $("#editMetaDataNotification");
                    element.removeClass("alert-success").addClass("alert-danger");
                    element.html("ExpirationData cannot be undefined.");
                    return;
                }
                // Collecting information
                var data = {
                    'OrderNumber': $('input[id=OrderNumber]').val(),
                    'CustomerPhone': $('input[id=CustomerPhone]').val(),
                    'CustomerEmail': $('input[id=CustomerEmail]').val(),
                    'LicSqlStdAmount': $('input[id=LicSqlStdAmount]').val(),
                    'LicSqlEntAmount': $('input[id=LicSqlEntAmount]').val(),
                    'LicWinAmount': $('input[id=LicWinAmount]').val(),
                    'ExpirationData': $('input[id=ExpirationData]').val(),
                    'OrgName': orgName
                };
                console.log(data);
                // Call for API
                $.ajax({
                    type: "POST",
                    url: "/update_metadata",
                    timeout: 240000,
                    data: data,
                    success: function () {
                        var element = $("#editMetaDataNotification");
                        element.removeClass("alert-danger").addClass("alert-success");
                        element.html("Metadata edited Successfully.");
                    },
                    error: function () {
                        var element = $("#editMetaDataNotification");
                        element.removeClass("alert-success").addClass("alert-danger");
                        element.html("Failed to edit Metadata!");
                    }
                });
            }
        }
    });
}

function addNewSp(param) {
    var vdcId = $(param).closest('tr').attr('id');
    console.log(vdcId);
    var dialogMessage = $("#addStorage-dialog-message");
    var storageSelector = $("#pvdcSp");
    var storageLimit = $("#newSpGbAmount");
    $(storageSelector).find('option').remove().end();
    storageSelector.append($('<option>', {
        value: 1,
        text: 'Loading...'
    }));
    $.ajax({
        type: "GET",
        url: "/get_sp",
        dataType: "json",
        success: function (response) {
            console.log("Retrieved.");
            $(storageSelector).find("option[value='1']").remove();
            console.log(response);
            $.each(response, function (n, h) {
                $(storageSelector).append($('<option>', {
                    value: h,
                    text: n
                }));
            });
        }
    });
    dialogMessage.dialog({
        modal: true,
        title: vdcId,
        width: 600,
        height: 425,
        buttons: {
            Close: function () {
                $(this).dialog("close");
            },
            Create: function () {
                var Data;
                var element = $("#newSpSetNotification");
                element.removeClass();
                element.html("");
                Data = {
                    'storageName': $(storageSelector).children(':selected').text(),
                    'storageHref': $(storageSelector).val(),
                    'storageLimit': $(storageLimit).val(),
                    'vdcId': vdcId
                };
                console.log(Data);
                $.ajax({
                    type: "POST",
                    url: "/add_storage_to_ovdc",
                    timeout: 240000,
                    data: Data,
                    success: function () {
                        var element = $("#newSpSetNotification");
                        element.addClass("alert-success");
                        element.html("Storage Profile Added successfully.");
                    },
                    error: function () {
                        var element = $("#newSpSetNotification");
                        element.addClass("alert-danger");
                        element.html("Failed to add Storage Profile!");
                    }
                });
            }
        }
    });
}
