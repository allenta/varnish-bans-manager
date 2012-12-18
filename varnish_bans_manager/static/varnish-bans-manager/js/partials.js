(function ($) {

  vbm.partials = vbm.partials || { registry: {} };

  /**
   *
   */
  vbm.partials.ready = function(id, options) {
    if (id in vbm.partials.registry) {
      var partial = vbm.partials.registry[id](options);
      vbm.ready(partial.callback, partial.ready, partial.unloader);
    }
  };

})(jQuery);

/******************************************************************************
 * Bans > Submit errors modal.
 ******************************************************************************/

(function ($) {
  vbm.partials.registry['bans-submit-errors-modal'] = function(options) {
    return {
      callback: function(context) {
        // On modal close, navigate to destination.
        $(context).filter('.modal').on('hidden', function () {
          vbm.navigation.navigate(options.destination);
        });
      }
    };
  };
})(jQuery);

/******************************************************************************
 * Users > Browse.
 ******************************************************************************/

(function ($) {
  vbm.partials.registry['users-browse-page'] = function(options) {
    return {
      callback: function(context) {
        var browser = $(context).find('.users-browser');

        (function (browser) {
          function get_data(page) {
            return {
              page: page || 1,
              items_per_page: browser.find('.collection-items-per-page li.active').attr('data-collection-items-per-page'),
              email: browser.find('.collection-filter input[name="email"]').val(),
              first_name: browser.find('.collection-filter input[name="first_name"]').val(),
              last_name: browser.find('.collection-filter input[name="last_name"]').val(),
              sort_criteria: browser.find('.collection-sort li.active').attr('data-sort-criteria'),
              sort_direction: browser.find('.collection-sort li.active').attr('data-sort-direction')
            };
          }

          function browse(page) {
            vbm.navigation.navigate(options.browse_url, {
              submit: get_data(page)
            });
          }

          function bulk(op) {
            // Collect input.
            var page = browser.find('.collection-pager li.active').attr('data-page');
            var submit = get_data(page);
            submit.op = op;
            if (browser.find('thead th.collection-selector input').is(':checked')) {
              submit.all_items = true;
            } else {
              submit.items = $.map(
                browser.find('tbody td.collection-selector input:checked'),
                function(input) { return $(input).attr('data-id'); });
            }
            // AJAX request.
            vbm.navigation.submit(options.bulk_url, submit);
          }

          function adjust_bulk_button(table) {
            var disabled = (table.find('tbody td.collection-selector input:checked').length === 0);
            browser.find('.collection-bulk button').toggleClass('disabled', disabled);
          }

          $('.collection-filter form', browser).submit(function() {
            browse();
            return false;
          });

          $('.collection-sort li', browser).click(function() {
            $(this).find('i:not(.icon-empty)').
              closest('li').
              toggleAttr('data-sort-direction', 'asc', 'desc');
            $(this).addClass('active').siblings('li').removeClass('active');
            browse();
            return false;
          });

          $('.collection-bulk li', browser).click(function() {
            bulk($(this).closest('li').attr('data-op'));
            return false;
          });

          $('.collection-items-per-page li', browser).click(function() {
            $(this).addClass('active').siblings('li').removeClass('active');
            browse();
            return false;
          });

          $('.collection-pager li:not(.disabled)', browser).click(function() {
            browse($(this).attr('data-page'));
            return false;
          });

          $('thead th.collection-selector input', browser).change(function() {
            var table = $(this).closest('table');
            table.find('tbody td.collection-selector input').attr('checked', $(this).is(':checked'));
            adjust_bulk_button(table);
          });

          $('tbody td.collection-selector input', browser).change(function() {
            var table = $(this).closest('table');
            if (!$(this).is(':checked')) {
              table.find('thead th.collection-selector input').attr('checked', false);
            }
            adjust_bulk_button(table);
          });
        })(browser);
      }
    };
  };
})(jQuery);
