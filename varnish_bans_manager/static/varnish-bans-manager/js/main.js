(function ($) {

  /******************************************************************************
   * BEHAVIORS.
   ******************************************************************************/

  vbm.attach_behaviors = function(context) {
    context = context || document;
    $.each(vbm.behaviors, function() {
      if ($.isFunction(this.attach)) {
        this.attach(context);
      }
    });
  };

  vbm.detach_behaviors = function(context) {
    context = context || document;
    $.each(vbm.behaviors, function() {
      if ($.isFunction(this.detach)) {
        this.detach(context);
      }
    });
  };

  /******************************************************************************
   * COMMANDS.
   ******************************************************************************/

  vbm.execute_commands = function(commands, context, library) {
    context = context || this;
    library = $.extend({}, vbm.commands, library);
    commands.sort(function(a, b) {
      return a.weight - b.weight;
    });
    var wait = false;
    for (var i in commands) {
      if (commands[i]['cmd'] && commands[i]['args'] && library[commands[i]['cmd']]) {
        wait = library[commands[i]['cmd']].apply(context, commands[i]['args']) || wait;
      }
    }
    return wait;
  };

  /******************************************************************************
   * READY.
   ******************************************************************************/

  vbm.ready = function(callback, is_ready, unloader) {
    function execute(callback, is_ready, unloader, context) {
      if ((typeof(is_ready) == 'function') && (is_ready() === false)) {
        // is_ready defined and not yet fulfilled. Try again in 100 ms.
        window.setTimeout(function() { execute(callback, is_ready, unloader, context); }, 100);
      } else {
        // Execute callback.
        if (vbm.client.browser.ie >= 1 && vbm.client.browser.ie <= 9) {
          callback($(document));
        } else {
          callback(context);
        }
        // Add unload behaviour.
        if (typeof(unloader) == 'function') {
          vbm.unload(unloader(context));
        }
      }
    }

    if (!vbm.behaviors.ready) {
      vbm.behaviors.ready = {
        callbacks: [],
        attach: function(context) {
          $(document).ready(function() {
            var callbacks = vbm.behaviors.ready.callbacks;
            delete vbm.behaviors.ready;
            for (var i = 0; i < callbacks.length; i++) {
              execute(callbacks[i]['callback'], callbacks[i]['is_ready'], callbacks[i]['unloader'], context);
            }
          });
        }
      };
    }

    vbm.behaviors.ready.callbacks.push({
      callback: callback,
      is_ready: is_ready,
      unloader: unloader
    });
  };

  vbm.unload = function(callback) {
    if (!vbm.behaviors.unload) {
      vbm.behaviors.unload = {
        callbacks: [],
        attach: function(context) {
          // Nothing to do here.
        },
        detach: function(context) {
          for (var i = 0; i < vbm.behaviors.unload.callbacks.length; i++) {
            var callback = vbm.behaviors.unload.callbacks[i];
            if (callback(context)) {
              vbm.behaviors.unload.callbacks.splice(i, 1);
              i--;
            }
          }
          if (vbm.behaviors.unload.callbacks.length === 0) {
            delete vbm.behaviors.unload;
          }
        }
      };
    }
    vbm.behaviors.unload.callbacks.push(callback);
  };

  /******************************************************************************
   * MODAL.
   ******************************************************************************/

  /**
   *
   */
  vbm.modal = {
    open: function(modal) {
      // Hide all previous modals.
      vbm.modal.close_all();
      // Append new modal in the overlay area.
      $('#overlay').append(modal);
      // Attach behaviors.
      // show() method called before attaching behaviors is
      // required to ensure behaviors such as bootstrap_form_tweaks
      // can access final width of elements.
      vbm.attach_behaviors(modal.show());
      // On close, detach behaviors & self-destroy modal.
      modal.on('hidden', function () {
        vbm.detach_behaviors(this);
        $(this).remove();
      });
      // Done!
      modal.modal('show');
    },
    close_all: function() {
      $('#overlay .modal').modal('hide');
    }
  };

  /******************************************************************************
   * SCROLL.
   ******************************************************************************/

  /**
   * Scrolls the window so that the referenced DOM object gets to the top.
   * The final scroll value will be altered by the offset given as second parameter.
   */
  vbm.scroll_to = function(id, offset) {
    if (vbm.client.system.ipad || vbm.client.system.iphone) {
      $("html,body").scrollTop($("#" + id).offset().top + offset);
    } else {
      $("html,body").animate({scrollTop: $("#" + id).offset().top + offset}, 'slow');
    }
  };

  /**
   *
   */
  vbm.scroll_top = function() {
    if (vbm.client.system.ipad || vbm.client.system.iphone) {
      $("html,body").scrollTop(0);
    } else {
      $("html,body").animate({scrollTop: 0}, 'slow');
    }
  };

  /******************************************************************************
   * GENERAL UTILITY STUFF.
   ******************************************************************************/

  /**
   *
   */
  vbm.register_overlay_handler = function(id, callback) {
    vbm.overlay_handlers[id] = callback;
  };

  /**
   *
   */
  vbm.close_all_overlays = function() {
    for (var id in vbm.overlay_handlers) {
      (vbm.overlay_handlers[id])();
    }
  };

  /******************************************************************************
   * JQUERY EXTENSIONS.
   ******************************************************************************/

  /**
   *
   */
  $.fn.toggleAttr = function(name, value1, value2) {
    var value = value1;
    if ($(this).attr(name) == value1) {
      value = value2;
    }
    return $(this).attr(name, value);
  };

  /**
   * Assigns and gets unique object id to any DOM element.
   */
  $.fn.oid = function() {
    if (this.length > 0) {
      var element = this.first();
      if (typeof(element.data('oid')) == 'undefined') {
        element.data('oid', 'oid#' + vbm.serial++);
      }
      return element.data('oid');
    }
  };

  /******************************************************************************
   * DOCUMENT LEVEL INITIALIZATIONS.
   ******************************************************************************/

  $(document).ready(function() {
    // Register document level overlay handlers.
    vbm.register_overlay_handler('notifications', vbm.notifications.close_all);
    vbm.register_overlay_handler('modals', function() { vbm.modal.close_all(); });
    vbm.register_overlay_handler('tooltips', function() { $('.tooltip').remove(); });
    vbm.register_overlay_handler('popovers', function() { $('[rel="popover"]').popover('hide'); });
    vbm.register_overlay_handler('dropdowns', function() { $('.dropdown').removeClass('open'); });
    vbm.register_overlay_handler('btn-groups', function() { $('.btn-group').removeClass('open'); });

    // Attach all behaviors.
    vbm.attach_behaviors(this);

    // Prepare AJAX navigation stuff.
    $(window).bind('statechange', vbm.navigation.statechange);

    // Initialize notifications container.
    $('#floating-notifications-container').notify({
      speed: 300,
      expires: 7000,
      stack: 'above'
    });

    // iPad & iPhone hacks.
    if (vbm.client.system.ipad || vbm.client.system.iphone) {
      $('body').on('touchstart.dropdown', '.dropdown-menu', function (e) { e.stopPropagation(); });
    }
  });

})(jQuery);
