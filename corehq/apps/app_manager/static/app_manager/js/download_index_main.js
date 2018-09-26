hqDefine('app_manager/js/download_index_main',[
    'jquery',
    'underscore',
    'ace-builds/src-min-noconflict/ace',
    'app_manager/js/download_async_modal',
    'app_manager/js/source_files',
],function ($, _, ace) {

    if (!ace.config.get('basePath')) { //TODO:Rohit move to base ace module(create if needed)
        //fetch ace path from requirejs configuration
        var acePath = requirejs.s.contexts._.config.paths["ace-builds/src-min-noconflict/ace"];
        ace.config.set("basePath",acePath.substring(0,acePath.lastIndexOf("/")));
    }

    $(function () {
        var elements = $('.prettyprint');
        _.each(elements, function (elem) {

            var editor = ace.edit(
                elem,
                {
                    showPrintMargin: false,
                    maxLines: 40,
                    minLines: 3,
                    fontSize: 14,
                    wrap: true,
                    useWorker: false,
                }
            );

            var fileName = $(elem).data('filename');
            if (fileName.endsWith('json')) {
                editor.session.setMode('ace/mode/json');
            } else {
                editor.session.setMode('ace/mode/xml');
            }
            editor.setReadOnly(true);
        });


    });

});