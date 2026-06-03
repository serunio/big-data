truncate table source_weights;

insert into source_weights (source, weight) values ('wikipedia', 0.6);
insert into source_weights (source, weight) values ('petmd', 0.8);
insert into source_weights (source, weight) values ('pubmed', 0.7);
