.. _davinci_json_diff:

.. highlight:: rst

.. role:: python(code)
    :language: python

.. role:: latex(code)
    :language: latex

JsonDiff
=========

This guide will help you on how to use jsondiff to generate differences between
versions of your resources on your crawler app.

1.Why we need that?
------------------

The crawling system generates a new version of some resources every time that the
crawler runs, so at the end of the process we need to gather that new information that
the crawler generated and consolidate the information on a new table, to speed-up the
process we can store what changed between versions of the resource and we can consolidate
only the information that has been changed.

With that requirement, we implemented an algorithm that takes two resources and generates
a diff containing all the information that has been changed, we can use this to improve our
consolidation process and also to have some history of modifications along the time.

Our algorithm uses a library called `jsondiff <https://github.com/xlwings/jsondiff>`_ that handle
this diff process for us.

2. How does it work?
-------------------

2.1. Transforming Django object to a dictionary
**********************************************

First of all, we need to have the two objects to compare, as we said on the previous section we use
the jsondiff library on the core of our algorithm so we need to compare two dict objects but what
we have on Django is the Django object, so the first step of the comparison is to translate the
object from Django to dict format, for that we use the Serializer.

2.2. Compute the difference using jsondiff
*****************************************

After that, we have the objects on dict format so we just call the jsondiff method to calculate
the difference. Note that we use the symmetric algorithm of jsondiff because it has a better
output format to us to work on.

2.3. Transforming jsondiff output
********************************

The jsondiff output is not on the best format for us, it's complex, so we need to transform that to
a simpler format, that's the third step of the algorithm we take the complex format of the jsondiff
and changes it to our format that you can find an example below:

.. code-block:: python

    {
          "all": {
            "inserts": {
              "column_name": {
                "new_value": 1111111
              }
            },
            "updates": {
              "column_name": {
                "old_value": 1,
                "new_value": 2
              }
            },
            "deletes": {
              "column_name": {
                "old_value": 1
              }
            }
          },
          "inserts": ["column_name"],
          "updates": ["column_name"],
          "deletes": ["column_name"]
   }

2.4. Storing the diff on the DB
******************************

After calculating the differences we store everything on the database inside the task table,
we store this data on the task that generated the new resource. We have four fields on the task
table that stores this data:

- differences_from_last_version: stores the dictionary that is inside the ``all`` key;
- inserted_fields: stores the list of fields that are inside the ``inserts`` key;
- updated_fields: stores the list of fields that are inside the ``updates`` key;
- deleted_fields: stores the list of fields that are inside the ``deletes`` key.

3. How to implement the jsondiff on a Crawler?
----------------------------------------------

The implementation of the jsondiff comparison is very simple, we will need just two steps to accomplish that:

3.1. Specify on your crawler the Serializer to use
**************************************************
To specify the serializer you just need to add a variable called ``__serializer_class__`` on your crawler's class,
like the example below:

.. code-block:: python

    class CrunchbaseOrganizationCrawler(Crawler):
        __crawler_name__ = CRAWLER_NAME

        __serializer_class__ = CrunchbaseOrganizationSerializerV1

In the example, I'm on the Crunchbase Crawler and I'm specifying that we should use the ``CrunchbaseOrganizationSerializerV1``
to serialize the objects to dictionary.

3.2. Get the previous version of your resource
**********************************************

To get the comparison you'll need the last version of the resource that you'll compare, the logic and the format
of your crawler
that is going to define on how you going to retrieve this previous version.

3.3. Call the comparison method
*******************************

We added a helper method inside the abstract crawler class, that just takes the two Django objects and
the task_id and generates and stores the jsondiff result. You'll call the ``register_differences`` method from
your crawler passing the two versions of the resource (previous and current) and the task_id that we'll
use to store the jsondiff result. Below you can find an example.

.. code-block:: python

    previous_organization = None
    # here we retrieve the previous version
    previous_organization = CrunchbaseOrganization.objects.filter(
        organization_id=organization_uuid)[0]
    # here we get the current version
    current_organization = CrunchbaseOrganization.create(**organization_data)

    # then if we have an previous version we call the register_differences method
    if previous_organization:
        self.register_differences(previous_object=previous_organization,
                                  current_object=current_organization,
                                  task_id=task_id)

3.4. What if I already have my version of diff
**********************************************

If you already have a way to calculate the diff you can use this method just to store the data on the task table,
just ignore the ``previous_object`` and ``current_object`` parameters and specify the ``already_computed_diff``.

**ATTENTION**: if you going to do this the ``already_computed_diff`` should be a dict and should contain four main keys,
that are the `all` that goes to the `differences_from_last_version` field and the `inserts`, `updates` and `deletes`
that goes to inserted_fields, updated_fields and deleted_fields.