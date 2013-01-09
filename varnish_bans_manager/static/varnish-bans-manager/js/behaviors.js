(function ($) {

  vbm.behaviors = vbm.behaviors || {};

  /******************************************************************************
   * NAVIGATION.
   ******************************************************************************/

  vbm.behaviors.navigation = {
    attach: function(context) {
      $('a.navigation', context).once('navigation', function() {
        $(this).click(function(event) {
          if ((event.which == 2) || event.metaKey) {
            return true;
          } else {
            event.preventDefault();
            vbm.navigation.navigate(
              $(this).attr('href'), {
                layout: $(this).attr('layout') || null
              });
            return false;
          }
        });
      });
    }
  };

  /******************************************************************************
   * AJAX FORM.
   ******************************************************************************/

  vbm.behaviors.form = {
    attach: function(context) {
      function complete(form, wait) {
        $(form)
          .find('input[name=_iframe_upload]').remove().end()
          .find(':input').removeAttr('disabled').end()
          .find('input[type=submit],button[type=submit]').removeClass('ajaxing').end()
          .removeClass('ajaxing');
        if (!wait) {
          $(form).stop(true, true).css('opacity', 1.0);
        }
      }

      $('form.ajax', context).once('ajax-form', function () {
        var form = this;
        var options = {
          url: $(this).attr('data-url'),
          data: { csrfmiddlewaretoken: vbm.csrf_token },
          beforeSerialize: function(form, options) {
            if (options.iframe) {
              // See http://jquery.malsup.com/form/#file-upload. Used in server side
              // to identify 'fake' AJAX requests.
              $(form).append('<input type="hidden" name="_iframe_upload" value="1"/>');
            }
          },
          beforeSubmit: function(arr, form, options) {
            vbm.notifications.close_all();
            $(form)
              .find(':input').attr('disabled', true).end()
              .find('input[type=submit], button[type=submit]').addClass('ajaxing').end()
              .addClass('ajaxing')
              .animate({opacity: 0.2}, 200);
          },
          success: function(response, status, xhr, form) {
            var wait = vbm.execute_commands(response, form, {});
            complete(form, wait);
          },
          error: function(xhr, status) {
            if (!xhr.aborted && (status != 'abort') && (status != 'aborted')) {
              vbm.notifications.notify('error', gettext("We are sorry, but the request couldn't be processed. Please, try again later."));
            }
            complete(form, false);
          },
          type: ($(this).attr('data-type') || 'POST').toUpperCase(),
          dataType: 'json',
          iframe: false
        };
        $(form).ajaxForm(options);
      });
    }
  };

  /******************************************************************************
   * CONFIRMATION DIALOGS.
   ******************************************************************************/

  vbm.behaviors.confirm = {
    attach: function(context) {
      $('a.confirm', context).once('confirm', function() {
        // Bind a click handler to show the confirmation modal.
        $(this).bind('click.confirm', function (event) {
          target = $(this);
          // Check if the action has already been confirmed.
          if (!target.data('confirmed')) {
            // Still not confirmed.
            // Extract options and set defaults.
            var title = target.attr('data-title') || gettext('Are you sure?');
            var text = target.attr('data-text') || gettext("This action can't be undone.");
            var cancel_button = target.attr('data-cancel-button') || gettext('Cancel');
            var confirm_button = target.attr('data-confirm-button') || gettext('Yes');
            // Open confirmation modal.
            vbm.modal.open($(
              '<div class="modal hide fade">' +
              '  <div class="modal-header">' +
              '    <h3>' + title + '</h3>' +
              '  </div>' +
              '  <div class="modal-body">' + text + '</div>' +
              '  <div class="modal-footer">' +
              '    <a href="#" class="btn" data-dismiss="modal"><i class="icon-remove"></i> ' + cancel_button + '</a>' +
              '    <a href="#" class="btn btn-danger btn-confirm"><i class="icon-ok icon-white"></i> ' + confirm_button + '</a>' +
              '  </div>' +
              '</div>').find('.btn-confirm').click(function () {
                // A click on the confirmation button will confirm the
                // action and launch the original click event again.
                target.data('confirmed', true).click();
              }).end());
            // Keep other handlers from executing.
            event.stopImmediatePropagation();
            event.preventDefault();
          } else {
            // Action has been confirmed. Let other handlers execute, but
            // first remove confirmation flag so that further clicks require
            // a new confirmation.
            target.data('confirmed', false);
          }
        });

        // We must ensure this click handler gets called first. The method
        // used for it has a dependency on an internal jQuery data structure,
        // so check it actually exists (as it may change on a library update).
        var handlers = $._data(this, "events");
        if (typeof handlers != 'undefined') {
          // If there are more handlers, move the new one to the top of the list.
          if (handlers.click.length > 1) {
            handlers.click.unshift(handlers.click.pop());
          }
        } else {
          // No jQuery support for data('events'). Unbind the click event as
          // we can't ensure it will work.
          $(this).unbind('click.confirm');
        }
      });
    }
  };

  /******************************************************************************
   * IMAGE FILE INPUT.
   ******************************************************************************/

  vbm.behaviors.image_file_input = {
    attach: function(context) {
      $('div.image-file-input', context).each(function () {
        // Find components.
        file_input = $(this).find('input[type="file"]');
        preview_link = $(this).find('.image-file-input-preview');
        delete_button = $(this).find('.image-file-input-delete');
        clear_input = $(this).find('.image-file-input-clear');

        // If a file has been previously uploaded, hide the file
        // input and show the image preview with the delete button.
        if (delete_button.length > 0) {
          clear_input.hide();
          file_input.hide();
          preview_link.show();
          delete_button.show();

          // Click handler for delete button.
          delete_button.click(function() {
            clear_input[0].checked = true;
            preview_link.hide();
            delete_button.hide();
            file_input.show();
            return false;
          });
        }
      });
    }
  };

  /******************************************************************************
   * AJAX LINK.
   ******************************************************************************/

  vbm.behaviors.link = {
    attach: function(context) {
      $('a.ajax', context).once('ajax-link', function () {
        $(this).click(function() {
          var url = $(this).attr('data-url');
          var type = ($(this).attr('data-type') || 'GET').toUpperCase();
          if ((type == 'POST') && $(this).hasClass('submit')) {
            vbm.navigation.submit(url, {});
          } else {
            vbm.ajax.call({
              url: url,
              type: type,
              element: this
            });
          }
          return false;
        });
      });
    }
  };

  /******************************************************************************
   * BOOTSTRAP INITIALIZATIONS.
   ******************************************************************************/

  vbm.behaviors.bootstrap_initializations = {
    attach: function(context) {
      // Popovers.
      $('.help-popover[rel="popover"]', context).once('bootstrap', function () {
        $(this).popover({
          trigger: 'hover',
          delay: { show: 500, hide: 100 }
        });
      });

      // Tooltips.
      $('.tip', context).tooltip();
      $('.tip-left', context).tooltip({ placement: 'left' });
      $('.tip-right', context).tooltip({ placement: 'right' });
      $('.tip-top', context).tooltip({ placement: 'top' });
      $('.tip-bottom', context).tooltip({ placement: 'bottom' });
    }
  };

  /******************************************************************************
   * BOOTSTRAP FORM TWEAKS.
   ******************************************************************************/

  vbm.behaviors.bootstrap_form_tweaks = {
    attach: function(context) {
      // Add an input-decoration wrapper to all prepends so that proper CSS avoids
      // wrong calculations of the input size.
      // See https://github.com/twitter/bootstrap/issues/4269.
      $('.input-prepend', context).once('input-decoration', function () {
        $(this).find('input').wrap('<div class="input-decoration-wrapper"></div>');
      });
    }
  };
})(jQuery);

/******************************************************************************
 * FIXED SIDEBAR.
 ******************************************************************************/

(function ($) {
  var item_height = 76;
  var collapsed_padding = 60;

  // Fix bar.
  function adjust_position(sidebar) {
    $(sidebar).css({
      'top': $('#content').offset().top,
      'left': $('#content').offset().left,
      'position': 'fixed'
    });
  }

  // Add/remove 'more' button.
  function adjust_items(sidebar) {
    // Fetch more button. Stop if not found.
    var more = $(sidebar).find('.btn-more');
    if (more.length > 0) {
      // Reset collapsed.
      var collapsed = $(sidebar).parent().find('> .collapsed');
      $(collapsed).fadeOut().data({is_visible: false});

      // Get current sidebar length & max length.
      var current_length = $(sidebar).find('.nav li').length;
      var max_length = Math.round(($(sidebar).innerHeight() - 80) / item_height);
      if (max_length < 2 ) {
        max_length = 2;
      }

      // Adjust.
      if (current_length > max_length) {
        pop_item(sidebar, collapsed, current_length - max_length);
      } else {
        push_item(sidebar, collapsed, max_length - current_length);
      }
      $(more).toggle($(collapsed).find('.nav li').length > 0);
    }
  }

  function pop_item(sidebar, collapsed, n) {
    // Do not pop item from sidebard in case the collapsed menu
    // will only contain one item.
    if ((n > 1) || ($(collapsed).find('.nav li').length > 0)) {
      var lis = $(sidebar).find('.nav li');
      var nav = $(collapsed).find('.nav');
      for(var i = lis.length - 2, j = 0; j < n; i--, j++) {
        $(nav).prepend(lis[i]);
      }
    }
  }

  function push_item(sidebar, collapsed, n) {
    // If after pushing to sidebar, collapsed menu will only contain
    // one item ==> push all collapsed items back to the sidebar.
    if ($(collapsed).find('.nav li').length - n === 1) {
      n += 1;
    }
    // Do it!
    var lis = $(collapsed).find('.nav li');
    var more = $(sidebar).find('.btn-more').parents('li');
    for(var i = 0, j = 0; j < n; i++, j++) {
      more.before(lis[i]);
    }
  }

  vbm.behaviors.fixed_sidebar = {
    attach: function(context) {
      $('.sidebar').once('sidebar', function () {
        // Add collapsed items container.
        $(this).after(
          '<div class="collapsed">' +
          '  <div class="arrow"></div>' +
          '  <ul class="nav nav-pills"></ul>' +
          '</div>'
        );

        // Set position & adjust items.
        adjust_position(this);
        adjust_items(this);

        // Button 'more' click event.
        $(this).find('.btn-more').bind('click', function(e) {
          e.preventDefault();
          var collapsed = $(this).parents('.sidebar').parent().find('> .collapsed');
          if ($(collapsed).find('.nav li').length > 0) {
            if ($(collapsed).data('is_visible') !== undefined && $(collapsed).data('is_visible')) {
              $(collapsed).data({is_visible: false});
              $(collapsed).fadeOut();
            } else {
              $(collapsed).data({is_visible: true});
              var offset = $(this).find('.icon').offset();
              $(collapsed).css({
                'top': offset.top - 15 - window.scrollY + 'px',
                'left': offset.left + collapsed_padding + 'px'
              }).fadeIn();
            }
          }
        });
      });

      $('body').once('sidebar', function () {
        $(window).resize(function() {
          var sidebar = $('.sidebar');
          if (sidebar.length > 0) {
            adjust_position(sidebar);
            adjust_items(sidebar);
          }
        });
      });
    }
   };
})(jQuery);
