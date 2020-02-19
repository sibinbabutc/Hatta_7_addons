openerp.hatta_web = function (instance) {
	instance.web.form.FieldMany2ManyBinaryMultiFiles = instance.web.form.FieldMany2ManyBinaryMultiFiles.extend({
		filetype: function(url){
            var url = url && url.filename || url;
            var tokens = typeof url == 'string' ? url.split('.') : [];
            if(tokens.length <= 1){
                return 'unknown';
            }
            var extension = tokens[tokens.length -1];
            if(extension.length === 0){
                return 'unknown';
            }else{
                extension = extension.toLowerCase();
            }
            var filetypes = {
                'webimage':     ['png','jpg','jpeg','jpe','gif'], // those have browser preview
                'image':        ['tif','tiff','tga',
                                 'bmp','xcf','psd','ppm','pbm','pgm','pnm','mng',
                                 'xbm','ico','icon','exr','webp','psp','pgf','xcf',
                                 'jp2','jpx','dng','djvu','dds'],
                'vector':       ['ai','svg','eps','vml','cdr','xar','cgm','odg','sxd'],
                'print':        ['dvi','pdf','ps'],
                'document':     ['doc','docx','odm','odt'],
                'presentation': ['key','keynote','odp','pps','ppt'],
                'font':         ['otf','ttf','woff','eot'],
                'archive':      ['zip','7z','ace','apk','bzip2','cab','deb','dmg','gzip','jar',
                                 'rar','tar','gz','pak','pk3','pk4','lzip','lz','rpm'],
                'certificate':  ['cer','key','pfx','p12','pem','crl','der','crt','csr'],
                'audio':        ['aiff','wav','mp3','ogg','flac','wma','mp2','aac',
                                 'm4a','ra','mid','midi'],
                'video':        ['asf','avi','flv','mkv','m4v','mpeg','mpg','mpe','wmv','mp4','ogm'],
                'text':         ['txt','rtf','ass'],
                'html':         ['html','xhtml','xml','htm','css'],
                'disk':         ['iso','nrg','img','ccd','sub','cdi','cue','mds','mdx'],
                'script':       ['py','js','c','cc','cpp','cs','h','java','bat','sh',
                                 'd','rb','pl','as','cmd','coffee','m','r','vbs','lisp'],
                'spreadsheet':  ['123','csv','ods','numbers','sxc','xls','vc','xlsx'],
                'binary':       ['exe','com','bin','app'],
            };
            for(filetype in filetypes){
                var ext_list = filetypes[filetype];
                for(var i = 0, len = ext_list.length; i < len; i++){
                    if(extension === ext_list[i]){
                        return filetype;
                    }
                }
            }
            return 'unknown';
        },
        
        get_image: function (session, model, field, id, resize) {
        	console.log(this)
        	r = this.options['size'] || '100,80'
        	console.log(r)
            return session.url('/web/binary/image', {model: model, field: field, id: id, resize: r});
        },
        
        attachments_resize_image: function (id, resize) {
            test = this.get_image(this.session, 'ir.attachment', 'datas', id, resize);
            return test
        },
        
		render_value: function () {
//			this._super.apply(this, arguments);
			var self = this;
	        this.read_name_values().then(function (datas) {
	        	for (var l in datas) { 
	        		var attach = datas[l];
	        		if (!attach.formating) {
	        			attach.filetype = self.filetype(attach.filename || attach.datas_fname || attach.name);
	        			attach.formating = true;
	        			attach.name = attach.filename || attach.datas_fname || attach.name
	        		}
	        	}
	        	console.log(datas)
	        	var render = $(instance.web.qweb.render('FieldBinaryFileUploader_prev.files', {'widget': self}));
	        	render.on('click', '.oe_delete', _.bind(self.on_file_delete, self));
	        	self.$('.oe_placeholder_files, .oe_attachments').replaceWith( render );
	        	
	        	var $input = self.$('input.oe_form_binary_file');
	            $input.after($input.clone(true)).remove();
	            self.$(".oe_fileupload").show();
	        })
    	},
    });
}

